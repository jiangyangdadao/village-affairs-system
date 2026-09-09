export function isMobile() {
  return window.innerWidth < 768
}

async function request(path, options = {}) {
  const opts = { credentials: 'same-origin', headers: {}, ...options }
  if (opts.body && !(opts.body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(opts.body)
  }
  const resp = await fetch(path, opts)
  if (resp.status === 401) { location.hash = '#/login'; throw new Error('请先登录') }
  if (resp.status === 507) { location.hash = '#/expired'; throw new Error('试用已到期') }
  if (!resp.ok) {
    let msg = '请求失败'
    try { msg = (await resp.json()).detail || msg } catch (e) { /* ignore */ }
    throw new Error(msg)
  }
  const ct = resp.headers.get('content-type') || ''
  return ct.includes('json') ? resp.json() : resp
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: 'POST', body }),
  put: (p, body) => request(p, { method: 'PUT', body }),
  del: (p) => request(p, { method: 'DELETE' }),
  upload: (p, form) => request(p, { method: 'POST', body: form }),
}
