import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

export async function POST(req: Request) {
  try {
    const url = new URL(req.url);
    const jobId = url.pathname.split('/').slice(-2)[0]; // Extract job ID from path
    const body = await req.json();
    const { success, error, kioskId } = body;

    if (!jobId) {
      return new Response(JSON.stringify({ error: 'Missing job ID' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Get the job
    const [job] = await sql`
      SELECT * FROM dispense_jobs WHERE id = ${jobId}
    `;

    if (!job) {
      return new Response(JSON.stringify({ error: 'Job not found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (success) {
      // Job completed successfully
      await sql`
        UPDATE dispense_jobs 
        SET status = 'completed', completed_at = NOW()
        WHERE id = ${jobId}
      `;

      // Update transaction status
      await sql`
        UPDATE transactions 
        SET status = 'completed', completed_at = NOW()
        WHERE id = ${job.transaction_id}
      `;

      return new Response(JSON.stringify({ 
        status: 'success',
        message: 'Job completed successfully' 
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });

    } else {
      // Job failed - increment retry count
      const newRetryCount = job.retry_count + 1;
      
      if (newRetryCount >= job.max_retries) {
        // Max retries reached - mark as failed
        await sql`
          UPDATE dispense_jobs 
          SET status = 'failed', retry_count = ${newRetryCount}, 
              error_message = ${error || 'Max retries exceeded'}
          WHERE id = ${jobId}
        `;

        await sql`
          UPDATE transactions 
          SET status = 'failed'
          WHERE id = ${job.transaction_id}
        `;

        return new Response(JSON.stringify({ 
          status: 'failed',
          message: 'Job failed after max retries' 
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });

      } else {
        // Retry available - reset to pending
        await sql`
          UPDATE dispense_jobs 
          SET status = 'pending', retry_count = ${newRetryCount},
              error_message = ${error || 'Retry attempt'}
          WHERE id = ${jobId}
        `;

        return new Response(JSON.stringify({ 
          status: 'retry',
          message: `Job will retry (attempt ${newRetryCount + 1}/${job.max_retries})` 
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }

  } catch (error) {
    console.error('Job completion error:', error);
    return new Response(JSON.stringify({ error: 'Failed to complete job' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
} 