import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const kioskId = req.headers.get('x-kiosk-id');

    if (!kioskId) {
      return new Response(JSON.stringify({ error: 'Missing kiosk ID' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
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
      return new Response(JSON.stringify(null), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Mark job as in progress
    await sql`
      UPDATE dispense_jobs 
      SET status = 'in_progress', last_attempt_at = NOW()
      WHERE id = ${job.id}
    `;

    return new Response(JSON.stringify({
      id: job.id,
      transaction_id: job.transaction_id,
      quarters: job.quarters,
      amount: job.amount,
      total: job.total,
      retry_count: job.retry_count,
      created_at: job.created_at
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Job polling error:', error);
    return new Response(JSON.stringify({ error: 'Failed to get pending jobs' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
} 