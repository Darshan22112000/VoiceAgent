// environment.prod.ts
export const environment = {
  production: true,
  apiUrl: (window as any).__env?.API_URL || '',
  vapiPublicKey: (window as any).__env?.VAPI_PUBLIC_KEY || '',
};