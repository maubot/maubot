FROM golang:1-alpine AS builder

RUN apk add --no-cache git ca-certificates gcc musl-dev
RUN wget -qO /usr/local/bin/dep https://github.com/golang/dep/releases/download/v0.4.1/dep-linux-amd64
RUN chmod +x /usr/local/bin/dep

COPY Gopkg.lock Gopkg.toml /go/src/maubot.xyz/
WORKDIR /go/src/maubot.xyz/
RUN dep ensure -vendor-only

COPY . /go/src/maubot.xyz/
RUN go build -o /usr/bin/maubot maubot.xyz/cmd/maubot


FROM alpine

RUN apk add --no-cache ca-certificates
COPY --from=builder /usr/bin/maubot /usr/bin/maubot

CMD ["/usr/bin/maubot", "-c", "/etc/maubot/config.yaml"]
