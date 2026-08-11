const http = require('http');
const fs = require('fs');
const path = require('path');
const vscode = require('vscode');

const HOST = '127.0.0.1';
const PORT = 47777;
const MAX_BODY_BYTES = 32 * 1024;
const WORKSPACE_ROOT = '/home/coder/code';
const TRACKS = new Set(['python', 'java']);

let server = null;
let output = null;

function sendJson(response, statusCode, body) {
  const json = JSON.stringify(body);

  response.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(json),
    'Cache-Control': 'no-store'
  });
  response.end(json);
}

function readJsonBody(request) {
  return new Promise((resolve, reject) => {
    let body = '';

    request.setEncoding('utf8');
    request.on('data', chunk => {
      body += chunk;

      if (Buffer.byteLength(body, 'utf8') > MAX_BODY_BYTES) {
        const error = new Error('Request body is too large.');
        error.statusCode = 400;
        reject(error);
        request.destroy();
      }
    });

    request.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch (_error) {
        const error = new Error('Request body must be valid JSON.');
        error.statusCode = 400;
        reject(error);
      }
    });

    request.on('error', reject);
  });
}

function getWorkspaceRoot() {
  const folder = vscode.workspace.workspaceFolders?.[0];
  return folder?.uri?.fsPath || WORKSPACE_ROOT;
}

function normalizePositiveInteger(value) {
  const number = Number(value || 0);
  return Number.isInteger(number) && number > 0 ? number : null;
}

function normalizeTrack(value) {
  const track = String(value || '').trim().toLowerCase();
  return TRACKS.has(track) ? track : '';
}

function normalizedWorkspaceInput(rawPath) {
  if (typeof rawPath !== 'string' || !rawPath.trim()) {
    const error = new Error('A file path is required.');
    error.statusCode = 400;
    throw error;
  }

  if (rawPath.includes('\0')) {
    const error = new Error('File path is malformed.');
    error.statusCode = 400;
    throw error;
  }

  return rawPath.trim().replace(/\\/g, '/').replace(/^\/+/, '');
}

function assertInsideWorkspaceBase(targetPath) {
  const workspaceBase = path.resolve(WORKSPACE_ROOT);
  const baseWithSeparator = workspaceBase.endsWith(path.sep)
    ? workspaceBase
    : `${workspaceBase}${path.sep}`;

  if (targetPath !== workspaceBase && !targetPath.startsWith(baseWithSeparator)) {
    const error = new Error('File path must stay inside the workspace.');
    error.statusCode = 403;
    throw error;
  }
}

function candidateRoots(rawTrack) {
  const roots = [];
  const addRoot = root => {
    if (!root) return;
    const resolved = path.resolve(root);
    if (!roots.includes(resolved)) roots.push(resolved);
  };

  addRoot(getWorkspaceRoot());

  const track = normalizeTrack(rawTrack);
  if (track) addRoot(path.join(WORKSPACE_ROOT, track));

  addRoot(WORKSPACE_ROOT);

  return roots;
}

function resolveWorkspaceFile(root, normalizedInput) {
  const workspacePath = path.resolve(root);
  const rootWithSeparator = workspacePath.endsWith(path.sep)
    ? workspacePath
    : `${workspacePath}${path.sep}`;
  const targetPath = path.resolve(workspacePath, normalizedInput);

  assertInsideWorkspaceBase(targetPath);

  if (targetPath !== workspacePath && !targetPath.startsWith(rootWithSeparator)) {
    const error = new Error('File path must stay inside the workspace.');
    error.statusCode = 403;
    throw error;
  }

  return targetPath;
}

async function prepareOpenFile(payload) {
  const normalizedInput = normalizedWorkspaceInput(payload.path);
  const candidates = candidateRoots(payload.track).map(root => resolveWorkspaceFile(root, normalizedInput));
  const wantsDirectory = payload.kind === 'directory' || normalizedInput.endsWith('/');
  let wrongKindMatch = false;

  for (const targetPath of candidates) {
    try {
      const stat = await fs.promises.stat(targetPath);

      if (wantsDirectory) {
        if (!stat.isDirectory()) {
          wrongKindMatch = true;
          continue;
        }

        return {
          targetPath,
          kind: 'directory',
          line: null,
          column: null
        };
      }

      if (!stat.isFile()) {
        wrongKindMatch = true;
        continue;
      }

      return {
        targetPath,
        kind: 'file',
        line: normalizePositiveInteger(payload.line),
        column: normalizePositiveInteger(payload.column)
      };
    } catch (error) {
      if (error && error.code === 'ENOENT') {
        continue;
      }

      throw error;
    }
  }

  if (wrongKindMatch) {
    const error = new Error(wantsDirectory ? 'Path must point to a directory.' : 'Path must point to a file.');
    error.statusCode = 400;
    throw error;
  }

  const notFound = new Error('File does not exist.');
  notFound.statusCode = 404;
  throw notFound;
}

async function openResolvedFile({ targetPath, kind, line, column }) {
  output?.appendLine(`opening ${targetPath}`);

  if (kind === 'directory') {
    await vscode.commands.executeCommand('revealInExplorer', vscode.Uri.file(targetPath));
    output?.appendLine(`revealed ${targetPath}`);
    return;
  }

  const document = await vscode.workspace.openTextDocument(vscode.Uri.file(targetPath));
  const options = { preview: false };

  if (line) {
    const lineIndex = Math.min(line - 1, Math.max(document.lineCount - 1, 0));
    const maxColumn = document.lineAt(lineIndex).text.length;
    const columnIndex = Math.min((column || 1) - 1, maxColumn);
    const position = new vscode.Position(lineIndex, columnIndex);

    options.selection = new vscode.Range(position, position);
  }

  await vscode.window.showTextDocument(document, options);
  output?.appendLine(`opened ${targetPath}`);
}

async function handleRequest(request, response) {
  const url = new URL(request.url || '/', 'http://localhost');
  const pathname = url.pathname.endsWith('/') && url.pathname !== '/'
    ? url.pathname.slice(0, -1)
    : url.pathname;

  if (request.method === 'GET' && pathname === '/health') {
    sendJson(response, 200, { ok: true });
    return;
  }

  if (request.method !== 'POST' || pathname !== '/open-file') {
    sendJson(response, 404, { ok: false, error: 'Not found.' });
    return;
  }

  try {
    const payload = await readJsonBody(request);
    const fileRequest = await prepareOpenFile(payload);

    output?.appendLine(`accepted ${fileRequest.targetPath}`);

    setTimeout(() => {
      openResolvedFile(fileRequest).catch(error => {
        output?.appendLine(`async open failed: ${error.message}`);
      });
    }, 0);

    sendJson(response, 200, { ok: true });
  } catch (error) {
    const statusCode = error.statusCode || 500;
    const message = statusCode === 500 ? 'Unable to open file.' : error.message;

    output?.appendLine(`open-file failed (${statusCode}): ${error.message}`);
    sendJson(response, statusCode, { ok: false, error: message });
  }
}

function activate(context) {
  output = vscode.window.createOutputChannel('Workshop Open File');
  server = http.createServer((request, response) => {
    handleRequest(request, response).catch(error => {
      output?.appendLine(`unexpected request failure: ${error.message}`);
      sendJson(response, 500, { ok: false, error: 'Unable to open file.' });
    });
  });

  server.on('error', error => {
    output?.appendLine(`server error: ${error.message}`);
  });

  server.listen(PORT, HOST, () => {
    output?.appendLine(`listening on http://${HOST}:${PORT}`);
  });

  context.subscriptions.push({
    dispose() {
      server?.close();
      server = null;
      output?.dispose();
      output = null;
    }
  });
}

function deactivate() {
  server?.close();
  server = null;
}

module.exports = {
  activate,
  deactivate
};
