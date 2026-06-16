// Proxies app2.nextaura.fit → IBM Code Engine app2-nextaura-fit
const CE_DOMAIN = '284w7l87aq94.us-south.codeengine.appdomain.cloud';
const BACKEND = 'app2-nextaura-fit';

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = new URL(url.pathname + url.search, `https://${BACKEND}.${CE_DOMAIN}`);
    const response = await fetch(new Request(target, request), { redirect: 'manual' });
    const headers = new Headers(response.headers);
    headers.set('X-Content-Type-Options', 'nosniff');
    headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  },
};
