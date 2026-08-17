import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 10 }, // ramp up to 10 concurrent virtual users
    { duration: "1m", target: 10 }, // hold steady
    { duration: "30s", target: 0 }, // ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<5000"], // 95% of requests under 5s
    http_req_failed: ["rate<0.05"], // less than 5% failure rate
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN;

export default function () {
  const sessionResp = http.post(`${BASE_URL}/api/v1/chat/sessions`, null, {
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
  });
  check(sessionResp, { "session created": (r) => r.status === 201 });

  const sessionId = sessionResp.json("id");

  const messageResp = http.post(
    `${BASE_URL}/api/v1/chat/sessions/${sessionId}/messages`,
    JSON.stringify({ content: "What is the claim number in my documents?" }),
    {
      headers: {
        Authorization: `Bearer ${ACCESS_TOKEN}`,
        "Content-Type": "application/json",
      },
    },
  );
  check(messageResp, { "message request succeeded": (r) => r.status === 200 });

  sleep(1);
}
