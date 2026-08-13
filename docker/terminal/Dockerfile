FROM alpine:3.20

# ttyd + tmux power the Terminal panel; curl/jq for poking the bot API and
# the Agent Memory Server from inside the compose network; redis for
# redis-cli against the workshop Redis; python for running the Redis
# Context Retriever client directly (Section 4's deploy step).
RUN apk add --no-cache ttyd tmux bash curl jq redis python3 py3-pip

# The Context Retriever python client (+ what src.context.deploy imports).
# Section 4: cd /workshop/code/python && python -m src.context.deploy
RUN python3 -m venv /opt/ctx && \
    /opt/ctx/bin/pip install --no-cache-dir \
        redis-context-retriever==0.0.6 redis python-dotenv
ENV PATH="/opt/ctx/bin:$PATH" \
    PYTHONPATH="/workshop/code/python"

COPY start.sh /start.sh
COPY tmux.conf /etc/tmux.conf
RUN chmod +x /start.sh

# Four ttyd instances back the workbench's terminal tabs
EXPOSE 7681 7682 7683 7684

CMD ["/start.sh"]
