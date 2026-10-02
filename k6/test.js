import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://192.168.37.10:30636/health', {
    headers: { 'Host': 'flask.local' },
  });
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body is ok': (r) => r.body === 'ok',
  });
  sleep(0.1);
}
