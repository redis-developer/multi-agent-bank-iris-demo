FROM alpine:3.20

# ttyd + tmux power the Terminal panel; curl/jq for poking the bot API and
# the Agent Memory Server from inside the compose network; redis for
# redis-cli against the workshop Redis.
RUN apk add --no-cache ttyd tmux bash curl jq redis

COPY start.sh /start.sh
COPY tmux.conf /etc/tmux.conf
RUN chmod +x /start.sh

# Four ttyd instances back the workbench's terminal tabs
EXPOSE 7681 7682 7683 7684

CMD ["/start.sh"]
