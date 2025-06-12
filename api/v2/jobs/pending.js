import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL);

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, x-kiosk-id');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const kioskId = req.headers['x-kiosk-id'];

    if (!kioskId) {
      return res.status(400).json({ error: 'Missing kiosk ID' });
    }

    // Update kiosk last seen
    await sql`
      INSERT INTO kiosks (id, last_seen_at, status) 
      VALUES (${kioskId}, NOW(), 'active')
      ON CONFLICT (id) 
      DO UPDATE SET last_seen_at = NOW(), status = 'active'
    `;

    // Get next pending job for this kiosk
    const [job] = await sql`
      SELECT dj.*, t.amount, t.total
      FROM dispense_jobs dj
      JOIN transactions t ON dj.transaction_id = t.id
      WHERE dj.kiosk_id = ${kioskId} 
        AND dj.status = 'pending' 
        AND dj.retry_count < dj.max_retries
      ORDER BY dj.created_at ASC
      LIMIT 1
    `;

    if (!job) {
      return res.status(200).json(null);
    }

    // Mark job as in progress
    await sql`
      UPDATE dispense_jobs 
      SET status = 'in_progress', last_attempt_at = NOW()
      WHERE id = ${job.id}
    `;

    return res.status(200).json({
      id: job.id,
      transaction_id: job.transaction_id,
      quarters: job.quarters,
      amount: job.amount,
      total: job.total,
      retry_count: job.retry_count,
      created_at: job.created_at
    });

  } catch (error) {
    console.error('Job polling error:', error);
    return res.status(500).json({ error: 'Failed to get pending jobs' });
  }
} 