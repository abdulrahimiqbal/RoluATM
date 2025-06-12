import { NextRequest, NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { amount } = body;
    const kioskId = req.headers.get('x-kiosk-id');

    if (!amount || amount <= 0) {
      return NextResponse.json({ error: 'Invalid amount' }, { status: 400 });
    }

    if (!kioskId) {
      return NextResponse.json({ error: 'Missing kiosk ID' }, { status: 400 });
    }

    // Create transaction in database
    const transactionId = crypto.randomUUID();
    const quarters = Math.ceil(amount / 0.25);
    const total = amount + 0.50; // Add 50 cent fee
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000); // 15 minutes

    await sql`
      INSERT INTO transactions (
        id, amount, quarters, total, status, kiosk_id, 
        created_at, expires_at, mini_app_url
      ) VALUES (
        ${transactionId}, ${amount}, ${quarters}, ${total}, 'pending', ${kioskId},
        NOW(), ${expiresAt.toISOString()}, 
        ${'https://mini-app-azure.vercel.app/pay/' + transactionId}
      )
    `;

    // Update kiosk last seen
    await sql`
      INSERT INTO kiosks (id, last_seen_at, status) 
      VALUES (${kioskId}, NOW(), 'active')
      ON CONFLICT (id) 
      DO UPDATE SET last_seen_at = NOW(), status = 'active'
    `;

    return NextResponse.json({
      id: transactionId,
      amount,
      quarters,
      total,
      mini_app_url: `https://mini-app-azure.vercel.app/pay/${transactionId}`,
      expires_at: expiresAt.toISOString(),
      status: 'pending'
    });

  } catch (error) {
    console.error('Transaction creation error:', error);
    return NextResponse.json(
      { error: 'Failed to create transaction' }, 
      { status: 500 }
    );
  }
} 