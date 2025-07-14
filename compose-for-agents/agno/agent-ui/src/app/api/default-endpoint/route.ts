import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ endpoint: process.env.DEFAULT_ENDPOINT });
}
