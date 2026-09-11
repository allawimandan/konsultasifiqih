/**
 * Server OAuth untuk Decap CMS di konsultasifiqih.com.
 *
 * Decap tidak bisa memakai GitHub langsung dari peramban — GitHub mewajibkan
 * penukaran kode otorisasi dilakukan di sisi server memakai client secret.
 * Worker kecil ini yang mengerjakannya.
 *
 * Dua alamat yang dipakai:
 *   /auth      -> melempar pengguna ke halaman izin GitHub
 *   /callback  -> menukar kode jadi token, lalu menyerahkannya ke Decap
 *
 * Yang wajib diisi di Cloudflare (Settings -> Variables) hanya SATU:
 *   GITHUB_CLIENT_SECRET
 *
 * Client ID tidak rahasia (ikut terlihat di URL izin GitHub), jadi ditulis
 * langsung di bawah sebagai nilai bawaan. Kalau suatu saat OAuth App-nya
 * diganti, cukup timpa dengan variabel GITHUB_CLIENT_ID di Cloudflare.
 */

const CLIENT_ID_BAWAAN = 'Ov23lig3H42CSazMXxJL';

const IZIN_GITHUB = 'https://github.com/login/oauth/authorize';
const TOKEN_GITHUB = 'https://github.com/login/oauth/access_token';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const clientId = env.GITHUB_CLIENT_ID || CLIENT_ID_BAWAAN;

    if (!clientId || !env.GITHUB_CLIENT_SECRET) {
      return teks('Worker belum diberi GITHUB_CLIENT_SECRET.', 500);
    }

    if (url.pathname === '/auth') {
      // state dipakai untuk memastikan callback berasal dari permintaan ini
      const state = crypto.randomUUID();
      const tujuan = new URL(IZIN_GITHUB);
      tujuan.searchParams.set('client_id', clientId);
      tujuan.searchParams.set('redirect_uri', url.origin + '/callback');
      tujuan.searchParams.set('scope', url.searchParams.get('scope') || 'repo,user');
      tujuan.searchParams.set('state', state);

      return new Response(null, {
        status: 302,
        headers: {
          Location: tujuan.toString(),
          'Set-Cookie': `cms_state=${state}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600`,
        },
      });
    }

    if (url.pathname === '/callback') {
      const kode = url.searchParams.get('code');
      const state = url.searchParams.get('state');
      const kuki = (request.headers.get('Cookie') || '').match(/cms_state=([^;]+)/);

      if (!kode) return serahkan('error', { message: 'Kode otorisasi tidak diterima dari GitHub.' });
      if (!kuki || kuki[1] !== state) {
        return serahkan('error', { message: 'State tidak cocok — coba masuk ulang.' });
      }

      let data;
      try {
        const r = await fetch(TOKEN_GITHUB, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'User-Agent': 'konsultasifiqih-cms',
          },
          body: JSON.stringify({
            client_id: clientId,
            client_secret: env.GITHUB_CLIENT_SECRET,
            code: kode,
            redirect_uri: url.origin + '/callback',
          }),
        });
        data = await r.json();
      } catch (err) {
        return serahkan('error', { message: 'Gagal menghubungi GitHub: ' + err.message });
      }

      if (!data || !data.access_token) {
        return serahkan('error', {
          message: (data && (data.error_description || data.error)) || 'GitHub tidak memberi token.',
        });
      }

      return serahkan('success', { token: data.access_token, provider: 'github' });
    }

    return teks('Server OAuth Decap CMS untuk konsultasifiqih.com.\nAlamat yang tersedia: /auth dan /callback.');
  },
};

function teks(isi, status = 200) {
  return new Response(isi, { status, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}

/**
 * Serahkan hasil ke jendela Decap yang membuka popup ini.
 * Urutannya sudah baku: popup menyapa dulu ("authorizing"), lalu membalas
 * hasilnya ke origin yang menyapa balik.
 */
function serahkan(status, muatan) {
  const pesan = `authorization:github:${status}:${JSON.stringify(muatan)}`;
  // escape '<' supaya isi pesan tak bisa menutup tag <script>
  const pesanJs = JSON.stringify(pesan).replace(/</g, '\\u003c');

  const html = `<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8"><title>Menyelesaikan masuk…</title></head>
<body style="font-family:system-ui,sans-serif;padding:40px;color:#333">
<p>Menyelesaikan proses masuk…</p>
<p style="color:#6c757d;font-size:14px">Jendela ini akan menutup sendiri.</p>
<script>
(function () {
  if (!window.opener) {
    document.body.innerHTML = '<p>Halaman ini harus dibuka dari editor, bukan langsung.</p>';
    return;
  }
  function balas(e) {
    window.opener.postMessage(${pesanJs}, e.origin);
    window.removeEventListener('message', balas, false);
  }
  window.addEventListener('message', balas, false);
  window.opener.postMessage('authorizing:github', '*');
})();
</script>
</body></html>`;

  return new Response(html, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
