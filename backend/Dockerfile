FROM golang:1.26.4-alpine

WORKDIR /app

RUN apk add --no-cache git

COPY go.mod go.sum ./

RUN go mod download

COPY . .

ARG VERSION=0.1.142
RUN go build -ldflags="-s -w -X main.Version=${VERSION} -X main.BuildType=release" -tags embed -o main ./cmd/server/

EXPOSE 8080

CMD ["./main"]