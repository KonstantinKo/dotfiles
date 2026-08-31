# Cloudflare R2 setup

Use a dedicated bucket for public agent artifacts.

R2 Standard storage includes 10 GB-month of storage, one million Class A
operations (including uploads), ten million Class B operations (including
downloads), and free internet egress each month. Stay on Standard storage; the
free tier does not apply to Infrequent Access. Check R2 usage periodically if the
bucket approaches 10 GB, because usage beyond the allowance is billed.

1. Install Wrangler, run `wrangler login`, and create an R2 Standard bucket.
2. Enable public access. For initial testing, the Cloudflare-managed `r2.dev` URL
   works; Cloudflare rate-limits it and does not recommend it for production.
3. For durable production links, add a domain you control to Cloudflare DNS and
   connect a subdomain such as `files.example.com` to the bucket as an R2 custom
   domain. Owning a domain alone is not enough; the zone must be available in the
   same Cloudflare account as the bucket.
4. Set these variables only when overriding the checked-in personal defaults:

   ```text
   R2_BUCKET
   FILE_PUBLIC_BASE_URL
   ```

   `FILE_PUBLIC_BASE_URL` is the public bucket origin, with no trailing path.
   `FILE_UPLOAD_PREFIX` can override the normal `temporary` or `durable` prefix.

Configure a lifecycle rule that expires `temporary/` objects after 14 days. Do
not apply expiry to `durable/`; those URLs may be referenced by historical PRs,
issues, and documentation.

Wrangler's OAuth session authenticates writes; the generated or custom public
hostname serves reads. Do not create a long-lived R2 API key unless another
client actually requires one.

Official references:

- https://developers.cloudflare.com/r2/buckets/public-buckets/
- https://developers.cloudflare.com/r2/pricing/
