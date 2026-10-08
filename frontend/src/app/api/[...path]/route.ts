import { NextRequest, NextResponse } from 'next/server';


async function forwardRequest(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const { path } = await context.params;
  // Use Vercel runtime service binding APP_URL / BACKEND_URL, with local fallback for standalone development
  const backendBase = process.env.APP_URL || process.env.BACKEND_URL || 'http://127.0.0.1:8000';

  // FastAPI routes in NeroSentinel are mounted under /api/...
  const subpath = path.join('/');
  const targetUrl = new URL(
    `api/${subpath}`,
    backendBase.endsWith('/') ? backendBase : `${backendBase}/`
  );
  targetUrl.search = request.nextUrl.search;

  const reqHeaders = new Headers(request.headers);
  reqHeaders.delete('host');
  reqHeaders.delete('connection');

  const body = ['GET', 'HEAD'].includes(request.method)
    ? undefined
    : await request.arrayBuffer();

  try {
    const upstream = await fetch(targetUrl, {
      method: request.method,
      headers: reqHeaders,
      body,
      cache: 'no-store',
    });

    return new NextResponse(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: upstream.headers,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: {
          code: 'BACKEND_SERVICE_UNREACHABLE',
          message: `Failed to reach backend service at ${targetUrl.origin}: ${
            error instanceof Error ? error.message : 'Unknown error'
          }`,
        },
      },
      { status: 502 }
    );
  }
}

export const GET = forwardRequest;
export const POST = forwardRequest;
export const PUT = forwardRequest;
export const PATCH = forwardRequest;
export const DELETE = forwardRequest;
export const OPTIONS = forwardRequest;
