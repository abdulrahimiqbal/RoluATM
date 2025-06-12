import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { transaction_id, proof, nullifier_hash, merkle_root } = body;

    if (!transaction_id) {
      return new Response(JSON.stringify({ error: 'Missing transaction ID' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get transaction
    const [transaction] = await sql`
      SELECT * FROM transactions 
      WHERE id = ${transaction_id} AND status = 'pending'
    `;

    if (!transaction) {
      return new Response(JSON.stringify({ error: 'Transaction not found or already processed' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Check if expired
    if (new Date(transaction.expires_at) < new Date()) {
      await sql`
        UPDATE transactions 
        SET status = 'expired' 
        WHERE id = ${transaction_id}
      `;
      return new Response(JSON.stringify({ error: 'Transaction expired' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // TODO: Verify World ID proof here
    // For now, we'll accept any proof in staging
    
    // Update transaction as paid
    await sql`
      UPDATE transactions 
      SET status = 'paid', nullifier_hash = ${nullifier_hash}, paid_at = NOW()
      WHERE id = ${transaction_id}
    `;

    // Create dispense job
    const jobId = crypto.randomUUID();
    await sql`
      INSERT INTO dispense_jobs (
        id, transaction_id, kiosk_id, quarters, status, 
        retry_count, max_retries, created_at
      ) VALUES (
        ${jobId}, ${transaction_id}, ${transaction.kiosk_id}, ${transaction.quarters}, 
        'pending', 0, 3, NOW()
      )
    `;

    return new Response(JSON.stringify({
      status: 'payment_complete',
      job_id: jobId,
      transaction_id,
      quarters: transaction.quarters
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Payment processing error:', error);
    return new Response(JSON.stringify({ error: 'Payment processing failed' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
} 