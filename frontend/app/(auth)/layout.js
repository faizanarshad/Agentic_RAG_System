import { connection } from 'next/server';

// Sign-in and password pages render per request so each response carries the CSP nonce set by proxy.js
export default async function AuthLayout({ children }) {
  await connection();
  return children;
}
