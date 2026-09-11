/* Skrip situs statis konsultasifiqih.com — mode gelap, pencarian, gambar cadangan. */
(function () {
  'use strict';

  /* ---------------- Mode gelap ---------------- */
  var tombolTema = document.getElementById('tombol-tema');
  if (tombolTema) {
    tombolTema.addEventListener('click', function () {
      var gelap = document.documentElement.getAttribute('data-tema') === 'gelap';
      var baru = gelap ? 'terang' : 'gelap';
      document.documentElement.setAttribute('data-tema', baru);
      try { localStorage.setItem('tema', baru); } catch (e) {}
    });
  }

  /* ---------------- Gambar yang gagal dimuat ---------------- */
  var GRADASI = [
    ['#7b2d3f', '#de214a'], ['#1f3a5f', '#2f6f9f'], ['#2f5d50', '#4e9c81'],
    ['#5a3b7c', '#9a6bbf'], ['#6b4423', '#c08457'], ['#3a3f58', '#6b7299'],
    ['#7c3626', '#d2703f'], ['#26525c', '#4e909c']
  ];
  function nomorDari(teks) {
    var n = 0, s = String(teks || '');
    for (var i = 0; i < s.length; i++) n = (n * 31 + s.charCodeAt(i)) >>> 0;
    return n;
  }
  document.addEventListener('error', function (e) {
    var im = e.target;
    if (!im || im.tagName !== 'IMG' || !im.parentNode) return;
    if (im.closest('.tulisan')) { im.style.display = 'none'; return; }
    var g = GRADASI[nomorDari(im.getAttribute('alt') || '') % GRADASI.length];
    var label = im.getAttribute('data-kategori') || 'Konsultasi Fiqih';
    im.parentNode.innerHTML =
      '<div class="ganti" style="background:linear-gradient(135deg,' + g[0] + ',' + g[1] + ')">' +
      '<span>' + label.replace(/[<>&"]/g, '') + '</span></div>';
  }, true);

  /* ---------------- Pencarian ---------------- */
  var kotakCari = document.getElementById('cari-kotak');
  var tombolCari = document.getElementById('tombol-cari');
  var input = document.getElementById('cari');

  if (tombolCari && kotakCari && input) {
    tombolCari.addEventListener('click', function () {
      kotakCari.classList.toggle('sembunyi');
      if (!kotakCari.classList.contains('sembunyi')) input.focus();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && input.value.trim()) {
        location.href = '/cari/?q=' + encodeURIComponent(input.value.trim());
      }
    });
  }

  /* halaman /cari/ */
  var wadahHasil = document.getElementById('cari-hasil');
  if (!wadahHasil) return;

  var status = document.getElementById('cari-status');
  var kolom = document.getElementById('cari-kata');
  var q = new URLSearchParams(location.search).get('q') || '';
  if (kolom) kolom.value = q;

  function amanTeks(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  var BULAN = ['Januari','Februari','Maret','April','Mei','Juni','Juli',
               'Agustus','September','Oktober','November','Desember'];
  function tanggalPanjang(iso) {
    var m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
    return m ? parseInt(m[3], 10) + ' ' + BULAN[parseInt(m[2], 10) - 1] + ' ' + m[1] : '';
  }

  var IKON_JAM = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';

  function kartu(r) {
    var gambar = r.g
      ? '<img src="/gambar/' + r.g + '" alt="' + amanTeks(r.j) + '" loading="lazy" data-kategori="' + amanTeks(r.k) + '">'
      : '<div class="ganti" style="background:linear-gradient(135deg,' +
        GRADASI[nomorDari(r.s) % GRADASI.length][0] + ',' +
        GRADASI[nomorDari(r.s) % GRADASI.length][1] + ')"><span>' + amanTeks(r.k) + '</span></div>';
    return '<article class="kartu">' +
      '<a class="kartu-gambar" href="/' + r.s + '/">' + gambar +
      '<span class="chip">' + amanTeks(r.k) + '</span></a>' +
      '<div class="kartu-isi"><h3><a href="/' + r.s + '/">' + amanTeks(r.j) + '</a></h3>' +
      '<span class="tanggal">' + IKON_JAM + tanggalPanjang(r.t) + '</span>' +
      '<p>' + amanTeks(r.r) + '</p></div></article>';
  }

  if (!q.trim()) {
    status.textContent = 'Ketik kata kunci di kolom atas, lalu tekan Enter.';
    return;
  }

  status.textContent = 'Mencari “' + q + '” …';
  fetch('/aset/cari.json')
    .then(function (r) {
      if (!r.ok) throw new Error('indeks tidak bisa dimuat');
      return r.json();
    })
    .then(function (data) {
      var kata = q.toLowerCase().split(/\s+/).filter(Boolean);
      var hasil = data.filter(function (r) {
        var ladang = (r.j + ' ' + r.k + ' ' + r.r + ' ' + (r.i || '')).toLowerCase();
        return kata.every(function (w) { return ladang.indexOf(w) !== -1; });
      });
      if (!hasil.length) {
        status.textContent = 'Tidak ada artikel yang cocok dengan “' + q + '”.';
        wadahHasil.innerHTML = '';
        return;
      }
      status.textContent = hasil.length + ' artikel ditemukan untuk “' + q + '”.';
      wadahHasil.className = 'kisi kisi-2';
      wadahHasil.innerHTML = hasil.slice(0, 60).map(kartu).join('');
    })
    .catch(function (err) {
      status.textContent = 'Pencarian gagal: ' + err.message;
    });
})();
