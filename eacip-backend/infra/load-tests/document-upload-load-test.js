import http from "k6/http";
import { check, sleep } from "k6";
import encoding from "k6/encoding";

export const options = {
  stages: [
    { duration: "20s", target: 5 },
    { duration: "40s", target: 5 },
    { duration: "20s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"], // upload response itself should be fast — Step 3's whole point was async processing
    http_req_failed: ["rate<0.05"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN;

const samplePdfBase64 =
  "JVBERi0xLjcKJfCflqQKNSAwIG9iago8PC9GaWx0ZXIgL0ZsYXRlRGVjb2RlL0xlbmd0aCA3NjUx"; // replace with a real small sample PDF, base64-encoded

export default function () {
  const data = {
    file: http.file(
      encoding.b64decode(samplePdfBase64, "std", "b"),
      "PTG-CLM-2026-4409.pdf",
      "application/pdf",
    ),
  };
  const resp = http.post(`${BASE_URL}/api/v1/documents`, data, {
    headers: { Authorization: `Bearer ${ACCESS_TOKEN}` },
  });
  check(resp, { "upload accepted": (r) => r.status === 201 });
  sleep(2);
}
