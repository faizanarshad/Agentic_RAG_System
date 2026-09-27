import { NextResponse } from 'next/server';

// Strict, nonce-based Content-Security-Policy for the pages that handle accounts and documents
// (sign-in, password reset, workspace, admin). Each response gets a fresh nonce; only scripts carrying it,
// and scripts they load ('strict-dynamic'), may run, so an injected <script> or inline handler is blocked.
// These pages render per request (see their layouts); the public site keeps its static CSP in next.config.mjs.
const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').origin;

export function proxy(request) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64');
  const isDev = process.env.NODE_ENV === 'development';
  const csp = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ''}`,
    // Style attributes cannot carry nonces; styles cannot run code, so inline styles stay allowed
    "style-src 'self' 'unsafe-inline'",
    `img-src 'self' data: blob: ${apiOrigin}`,
    "font-src 'self'",
    `connect-src 'self' ${apiOrigin}${isDev ? ' ws: wss:' : ''}`,
    "frame-ancestors 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "object-src 'none'",
    ...(isDev ? [] : ['upgrade-insecure-requests']),
  ].join('; ');

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-nonce', nonce);
  requestHeaders.set('Content-Security-Policy', csp);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set('Content-Security-Policy', csp);
  response.headers.set('Cache-Control', 'private, no-store');
  return response;
}

export const config = {
  matcher: [
    {
      source: '/(login|forgot-password|reset-password|workspace|admin)(.*)',
      missing: [
        { type: 'header', key: 'next-router-prefetch' },
        { type: 'header', key: 'purpose', value: 'prefetch' },
      ],
    },
  ],
};
