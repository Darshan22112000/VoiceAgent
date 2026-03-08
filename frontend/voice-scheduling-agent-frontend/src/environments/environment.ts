// export const environment = {
//   production: true,
//   apiUrl: (window as any).__env?.API_URL || 'http://localhost:8000',
//   vapiPublicKey: (window as any).__env?.VAPI_PUBLIC_KEY || '',
// };
export const environment = {
  production: false,
  apiUrl: '/api',    // ✅ same origin now — no CORS, no cookie issues
  vapiPublicKey: (window as any).__env?.VAPI_PUBLIC_KEY || '',
};