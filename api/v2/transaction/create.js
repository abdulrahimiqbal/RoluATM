import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL);

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-kiosk-id');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { amount } = req.body;
    const kioskId = req.headers['x-kiosk-id'];

    if (!amount || amount <= 0) {
      return res.status(400).json({ error: 'Invalid amount' });
    }

    if (!kioskId) {
      return res.status(400).json({ error: 'Missing kiosk ID' });
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

    return res.status(200).json({
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
    return res.status(500).json({ error: 'Failed to create transaction' });
  }
} 