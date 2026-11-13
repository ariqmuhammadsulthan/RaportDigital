// Report editor/layout adapted from Ganosec19/RaportDigital; see docs/origins.md.
const program = document.body.dataset.program;
const year = Number(document.body.dataset.year);
const senior = program.startsWith("c-");
const A = program === "c-ipa";
const track = senior ? (A ? " MIA" : " IIS") : "";
const KL =
  program === "a"
    ? ["I", "II", "III", "IV", "V", "VI"]
    : program === "b"
      ? ["VII", "VIII", "IX"]
      : ["X", "XI", "XII"];
const $ = (id) => document.getElementById(id),
  esc = (s) =>
    String(s == null ? "" : s).replace(
      /[&<>"]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
    );
const nz = (s) =>
  String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
const mk = (n, sp, kk) => ({
  n: n || "",
  kkm: kk,
  a: n ? "Menunjukkan penguasaan yang sangat baik pada materi " + n + "." : "",
  b: n ? "Perlu bimbingan lebih lanjut dalam memahami materi " + n + "." : "",
  sp: sp ? 1 : 0,
});
const U = senior
  ? [
      "Pendidikan Agama dan Budi Pekerti",
      "Pendidikan Kewarganegaraan",
      "Bahasa Indonesia",
      "Matematika",
      "Sejarah Indonesia",
      "Bahasa Inggris",
    ]
  : [
      "Pendidikan Agama dan Budi Pekerti",
      "Pendidikan Kewarganegaraan",
      "Bahasa Indonesia",
      "Matematika",
      ...(program === "a" ? ["IPAS"] : ["IPA", "IPS"]),
      "Bahasa Inggris",
    ];
const PM = {
  IPA: ["Matematika Peminatan", "Fisika", "Kimia", "Biologi"],
  IPS: ["Geografi", "Sejarah", "Sosiologi", "Ekonomi"],
};
const K = [
  "Public Speaking (Pemberdayaan)",
  "Keterampilan Wajib (SBK, PJOK, Prakarya & Kewirausahaan)",
  "Teknologi Informasi dan Komunikasi",
];
const grp = (a, kk) => [
  ...a.map((n) => mk(n, 0, kk)),
  mk("", 1, kk),
  mk("", 1, kk),
];
const mkms = (kk) => ({
  u: grp(U, kk),
  p: senior ? grp(PM[A ? "IPA" : "IPS"], kk) : [],
  k: grp(K, kk),
  e: [
    { n: "", p: "", k: "" },
    { n: "", p: "", k: "" },
    { n: "", p: "", k: "" },
  ],
  tgl: "",
  batas: 80,
});
const mkc = (kl) => {
  const kk = kl == "XII" ? 73 : 70;
  return {
    st: [],
    wali: "",
    nip: "-",
    tahun: year + "/" + (year + 1),
    naik: "",
    ms: { Ganjil: mkms(kk), Genap: mkms(kk) },
  };
};
const def = () => ({
  logo: "",
  sch: {
    nama: "",
    npsn: "",
    a1: "",
    a2: "",
    a3: "",
    ar: "",
    pos: "",
    web: "",
    email: "",
    tel: "",
    kepala: "",
    nipk: "",
    tempat: "",
    sem: "Ganjil",
    kelas: KL[0],
  },
  c: Object.fromEntries(KL.map((k) => [k, mkc(k)])),
});
let S = def();
const emp = (student) =>
  Object.entries(student).every(([key, value]) =>
    key === "n"
      ? Object.values(value).every((scores) =>
          Object.values(scores).every((v) => !v),
        )
      : !value,
  );
const D = () => S.c[S.sch.kelas],
  M = () => D().ms[S.sch.sem];
const opt = (v, c) => `<option${v == c ? " selected" : ""}>${v}</option>`;
const F = [
  ["nama", "Nama PKBM"],
  ["npsn", "NPSN"],
  ["a1", "Alamat baris 1"],
  ["a2", "Alamat baris 2"],
  ["a3", "Alamat baris 3 (provinsi + kode pos)"],
  ["ar", "Alamat singkat pada halaman nilai"],
  ["pos", "Kode pos"],
  ["web", "Website"],
  ["email", "Email"],
  ["tel", "Telepon"],
  ["kepala", "Kepala sekolah"],
  ["nipk", "NIP kepala sekolah"],
  ["tempat", "Kota tempat tanda tangan"],
];
const G = [
  ["u", "Kelompok Mata Pelajaran Umum"],
  ["p", "Peminatan " + (A ? "Ilmu-Ilmu Alam" : "Ilmu-Ilmu Sosial")],
  ["k", "Kelompok Khusus"],
];
if (!senior) G.splice(1, 1);
const allM = () => [...M().u, ...M().p, ...M().k].filter((r) => r.n);
function setup() {
  const c = S.sch,
    d = D(),
    m = M(),
    o = c.sem == "Ganjil" ? "Genap" : "Ganjil";
  const I = (a, k, l, v, t) =>
    `<label>${l}<input ${t ? `type="${t}" ` : ""}data-${a}="${k}" value="${esc(v)}"></label>`;
  let h =
    `<h3>Data PKBM (sama untuk semua kelas)</h3><div class="g">` +
    F.map(([k, l]) => I("p", k, l, c[k])).join("") +
    `<label>Logo PKBM (PNG atau JPG)<input type="file" accept="image/png,image/jpeg" data-action="logo"></label></div>` +
    (S.logo
      ? `<div class="row"><img src="${esc(S.logo)}" style="height:60px;background:#fff;border-radius:6px"><button data-action="remove-logo">Hapus logo</button></div>`
      : "");
  h += `<h3>Kelas ${c.kelas} ${track} (semua semester)</h3><div class="g">${I("w", "wali", "Wali kelas", d.wali)}${I("w", "nip", "NIP wali kelas", d.nip)}</div>${d.naik ? '<p>Teks kelas dari buku lama (arsip lama): '+esc(d.naik)+'</p>' : ''}`;
  h += `<h3>Kelas ${c.kelas} · Semester ${c.sem}</h3><div class="g">${I("x", "tgl", "Tanggal rapor, mis. 21 Desember 2026", m.tgl)}${I("x", "batas", "Batas nilai deskripsi tinggi", m.batas, "number")}</div>`;
  h +=
    '<p class="mu">Baris berlatar abu-abu adalah kolom cadangan: kosongkan nama mapelnya dan baris itu tidak tercetak. Baris cadangan yang sudah diberi nama hanya tercetak untuk siswa yang punya nilainya.</p>';
  h += G.map(
    ([g, t]) =>
      `<h3>${t}</h3><div class="ov"><table class="mt"><thead><tr><th>Mata pelajaran</th><th style="width:60px">KKM</th><th>Capaian (nilai ≥ batas)</th><th>Capaian (nilai &lt; batas)</th></tr></thead>` +
      m[g]
        .map(
          (r, i) =>
            `<tr${r.sp ? ' class="sp"' : ""}><td><input data-m="${g}.${i}.n" value="${esc(r.n)}" placeholder="${r.sp ? "(cadangan)" : ""}"></td><td><input type="number" data-m="${g}.${i}.kkm" value="${esc(r.kkm)}"></td><td><textarea rows="2" data-m="${g}.${i}.a">${esc(r.a)}</textarea></td><td><textarea rows="2" data-m="${g}.${i}.b">${esc(r.b)}</textarea></td></tr>`,
        )
        .join("") +
      "</table></div>",
  ).join("");
  h +=
    '<h3>Ekstrakurikuler</h3><div class="ov"><table class="mt"><thead><tr><th>Kegiatan</th><th>Keterangan</th></tr></thead>' +
    m.e
      .map(
        (e, i) =>
          `<tr><td><input data-e="${i}.n" value="${esc(e.n)}"></td><td><textarea rows="2" data-e="${i}.k">${esc(e.k)}</textarea></td></tr>`,
      )
      .join("") +
    "</table></div>";
  h += `<div class="row"><button data-action="copy">Salin mapel dan ekstrakurikuler semester ${c.sem} ke semester ${o}</button></div>`;
  $("t1").innerHTML = h;
}
function cpm() {
  const o = S.sch.sem == "Ganjil" ? "Genap" : "Ganjil";
  const target = D().ms[o];
  for (const key of ["u", "p", "k", "e"]) {
    const changed = target[key].some((entry, i) =>
      entry.n !== M()[key][i]?.n && D().st.some(student => student.n?.[o]?.[key + i])
    );
    if (changed) return alert("Penyalinan akan mengubah nama mapel atau kegiatan yang sudah memiliki nilai di semester " + o + ".");
  }
  if (
    confirm("Timpa pengaturan semester " + o + " kelas " + S.sch.kelas + "?")
  ) {
    D().ms[o] = JSON.parse(JSON.stringify(M()));
    save();
  }
}
function logo(i) {
  const f = i.files[0];
  if (!f) return;
  if (f.size > 4000000 || !["image/png", "image/jpeg"].includes(f.type)) {
    alert("Gunakan PNG/JPG hingga 4 MB.");
    return;
  }
  const r = new FileReader();
  r.onload = () => {
    const im = new Image();
    im.onload = () => {
      const k = Math.min(1, 700 / Math.max(im.width, im.height)),
        c = document.createElement("canvas");
      c.width = im.width * k;
      c.height = im.height * k;
      c.getContext("2d").drawImage(im, 0, 0, c.width, c.height);
      S.logo = c.toDataURL("image/png");
      save();
      setup();
    };
    im.src = r.result;
  };
  r.readAsDataURL(f);
}
document.addEventListener("input", (e) => {
  const t = e.target,
    d = t.dataset;
  if (!d) return;
  if (d.p) {
    S.sch[d.p] = t.value;
  } else if (d.w) {
    D()[d.w] = t.value;
  } else if (d.x) {
    M()[d.x] = d.x == "batas" ? +t.value : t.value;
  } else if (d.m) {
    const [g, i, f] = d.m.split(".");
    M()[g][i][f] = f == "kkm" ? +t.value : t.value;
  } else if (d.e) {
    const [i, f] = d.e.split(".");
    M().e[i][f] = t.value;
  } else if (d.r !== undefined) {
    const L = D().st,
      r = +d.r;
    while (L.length <= r) L.push({ n: {} });
    cols()[+d.c].s(L[r], t.value);
    cnt();
  } else return;
  save();
});
document.addEventListener("click", (e) => {
  const d = e.target.dataset && e.target.dataset.del;
  if (d !== undefined && d !== "") {
    if (!confirm("Hapus siswa ini beserta nilai kedua semester?")) return;
    D().st.splice(+d, 1);
    save();
    lst();
  }
});
const dt = (v) => {
  v = String(v || "").trim();
  return /^\d{5}$/.test(v)
    ? new Date((+v - 25569) * 864e5).toLocaleDateString("id-ID", {
        day: "numeric",
        month: "long",
        year: "numeric",
        timeZone: "UTC",
      })
    : v;
};
const num = (v) => String(v).trim().replace(",", ".");
const sn = (s, k, v) => {
  s.n = s.n || {};
  const m = (s.n[S.sch.sem] = s.n[S.sch.sem] || {});
  m[k] = v;
};
const IDC = [
  ["Nama", "nama"],
  ["NIPD", "nipd"],
  ["NISN", "nisn"],
  ["No Rapor", "norap"],
  ["JK", "jk"],
  ["Tempat Lahir", "tl"],
  ["Tanggal Lahir", "tgl"],
  ["Agama", "agama"],
  ["Anak Ke", "anak"],
  ["Alamat", "alamat"],
  ["Telepon", "tel"],
  ["Diterima di Kelas", "dk"],
  ["Tanggal Diterima", "dtg"],
  ["Nama Ayah", "ayah"],
  ["Nama Ibu", "ibu"],
  ["Pekerjaan Ayah", "kayah"],
  ["Pekerjaan Ibu", "kibu"],
  ["Nama Wali", "wali"],
  ["Pekerjaan Wali", "kwali"],
];
const ns = (s) => (s.n || {})[S.sch.sem] || {};
const markKey = (r) => {
  for (const [group] of G) {
    const index = M()[group].indexOf(r);
    if (index >= 0) return group + index;
  }
};
const allColumns = () => [
  ...IDC.map(([h, k]) => ({
    h,
    w: ["nama", "alamat", "ayah", "ibu", "wali"].includes(k) ? "w" : "",
    g: (s) => s[k] || "",
    s: (s, v) => {
      s[k] = k == "tgl" || k == "dtg" ? dt(v) : v;
    },
  })),
  ...allM().map((r) => ({
    h: r.n,
    score: true,
    w: "v",
    g: (s) => ns(s)[markKey(r)] || "",
    s: (s, v) => sn(s, markKey(r), num(v)),
  })),
  ...M().e.flatMap((e, i) =>
    e.n
      ? [
          {
            h: "Predikat " + e.n,
            w: "v",
            g: (s) => ns(s)["e" + i] || "",
            s: (s, v) => sn(s, "e" + i, v),
          },
        ]
      : [],
  ),
  ...["Izin", "Sakit", "Alpa"].map((h) => ({
    h,
    w: "v",
    g: (s) => ns(s)[h.toLowerCase()] || "",
    s: (s, v) => sn(s, h.toLowerCase(), v),
  })),
  {
    h: "Catatan wali kelas",
    w: "w",
    g: (s) => ns(s).catatan || "",
    s: (s, v) => sn(s, "catatan", v),
  },
];
function cols() {
  const columns = allColumns();
  const start = IDC.length;
  const end = start + allM().length;
  switch ($("columns").value) {
    case "identity":
      return columns.slice(0, start);
    case "marks":
      return [columns[0], ...columns.slice(start, end)];
    case "notes":
      return [columns[0], ...columns.slice(end)];
    default:
      return columns;
  }
}
$("columns").addEventListener("change", lst);
const LS = () => D().st.filter((s) => s.nama);
const cnt = () => {
  $("sc").textContent =
    LS().length +
    " siswa · kelas " +
    S.sch.kelas +
    track +
    " · semester " +
    S.sch.sem;
};
function more() {
  if (Math.max(D().st.length, S.rows || 30) >= 1000) return;
  S.rows = Math.min(1000, Math.max(D().st.length, S.rows || 30) + 10);
  save();
  lst();
}
function clr() {
  if (confirm("Hapus semua siswa kelas " + S.sch.kelas + "?")) {
    D().st = [];
    save();
    lst();
  }
}
function lst() {
  const C = cols(),
    L = D().st,
    n = Math.max(L.length, S.rows || 30);
  cnt();
  $("gh").innerHTML =
    "<tr><th>No</th>" +
    C.map((c) => `<th>${esc(c.h)}</th>`).join("") +
    "<th></th></tr>";
  let h = "";
  for (let i = 0; i < n; i++) {
    const s = L[i] || {};
    h +=
      `<tr><td class="n">${i + 1}</td>` +
      C.map(
        (c, j) =>
          `<td class="${c.w}"><input aria-label="${esc(c.h)} · baris ${i + 1}" data-r="${i}" data-c="${j}" value="${esc(c.g(s))}"></td>`,
      ).join("") +
      `<td>${L[i] ? `<button aria-label="Hapus siswa baris ${i + 1}" data-del="${i}">×</button>` : ""}</td></tr>`;
  }
  $("gb").innerHTML = h;
}
document.addEventListener("paste", (e) => {
  const t = e.target,
    d = t.dataset;
  if (!d || d.r === undefined) return;
  e.preventDefault();
  const R = (e.clipboardData.getData("text") || "")
    .replace(/\r/g, "")
    .replace(/\n+$/, "")
    .split("\n")
    .map((r) => r.split("\t"));
  const C = cols(),
    r0 = +d.r,
    c0 = +d.c,
    L = D().st;
  if (R.length > 1001) return alert("Batas 1.000 siswa per kelas.");
  const width = R.reduce((max, row) => Math.max(max, row.length), 0);
  const targets = C.slice(c0, c0 + width);
  if (targets.length !== width) return alert("Kolom yang ditempel melebihi tabel.");
  const headers = R[0].map(nz);
  const hasHeader = R.length > 1 && headers.some(h => C.some(c => nz(c.h) === h));
  if (hasHeader) {
    if (headers.length !== width || headers.some((h,i) => h !== nz(targets[i].h)))
      return alert("Urutan judul kolom berbeda. Sesuaikan dengan tabel sebelum menempel.");
    R.shift();
  } else if (width > 1 && targets.some(c => c.score)) {
    if (!confirm("Tempel nilai tanpa judul sesuai urutan ini?\n" + targets.map(c => c.h).join(" → "))) return;
  }
  if (R.some(row => row.some((cell,i) => targets[i].score && cell.trim() &&
      (!/^\d+(?:[.,]\d+)?$/.test(cell.trim()) || Number(num(cell.trim())) > 100))))
    return alert("Nilai tidak valid. Periksa judul kolom dan rentang 0–100.");
  if (r0 + R.length > 1000) {
    alert("Batas 1.000 siswa per kelas.");
    return;
  }
  R.forEach((row, i) =>
    row.forEach((v, j) => {
      const c = C[c0 + j];
      if (!c) return;
      while (L.length <= r0 + i) L.push({ n: {} });
      c.s(L[r0 + i], v.trim());
    }),
  );
  save();
  lst();
});
/* Cetak */
const nv = (s, r) => ns(s)[markKey(r)] || "";
const wm = () => (S.logo ? `<img class="wm" src="${esc(S.logo)}">` : "");
const v = (x) => esc(x || "-");
const legacyPrint = () => Number(document.body.dataset.issue) > 0 && S.reportVersion !== 2;
const cov = (s, i) => {
  const c = S.sch;
  return `<div class="pg cv"><div class="nr"><table><tr><th class="y">No Rapor</th><th>Nomor Pokok Sekolah Nasional</th></tr><tr><td>${v(s.norap || (legacyPrint() ? i + 1 : ""))}</td><td>${v(c.npsn)}</td></tr></table></div>${S.logo ? `<img class="lg" src="${esc(S.logo)}">` : '<div class="lg0">Logo PKBM<br>(unggah di tab Pengaturan)</div>'}<div class="ttl">LAPORAN HASIL BELAJAR PESERTA DIDIK<br>PROGRAM ${program === "a" ? "PAKET A SETARA SD" : program === "b" ? "PAKET B SETARA SMP" : "PAKET C SETARA SMA"}</div><div class="lb">NAMA PESERTA DIDIK</div><div class="pc nm">${esc(s.nama)}</div><div class="lb" style="margin-top:3mm">NIPD / NISN</div><div class="pc ni">${v(s.nipd)} / ${v(s.nisn)}</div><div class="sc"><div class="sn">${esc(c.nama)}</div><div class="dl">NPSN ${esc(c.npsn)}</div><div class="dl">${esc(c.a1.toUpperCase())}</div><div class="dl">${esc(c.a2.toUpperCase())}</div><div class="dl">${esc(c.a3.toUpperCase())}</div></div></div>`;
};
const sek = () => {
  const c = S.sch,
    r = [
      ["Nama Satuan Pendidikan", esc(c.nama)],
      ["NPSN", esc(c.npsn)],
      ["Alamat", esc(c.a1) + "<br>" + esc(c.a2) + "<br>" + esc(c.a3)],
      ["Kode Pos", esc(c.pos)],
      ["Website", esc(c.web)],
      ["email", esc(c.email)],
      ["Telepon", esc(c.tel)],
    ];
  return `<div class="pg id">${wm()}<div class="yb"></div><div><h3 class="ctr">IDENTITAS SEKOLAH</h3><table class="kd">${r.map(([k, x]) => `<tr><td>${k}</td><td>:</td><td>${x}</td></tr>`).join("")}</table></div><div class="yb"></div></div>`;
};
const ktr = (s) => {
  const c = S.sch,
    g = D().ms.Ganjil.tgl,
    jk = { L: "Laki-Laki", P: "Perempuan" }[(s.jk || "").toUpperCase()] || s.jk;
  const r = [
    ["Nama Peserta Didik", v(s.nama)],
    ["Nomor Induk Peserta Didik", v(s.nipd)],
    ["NISN", v(s.nisn)],
    ["Tempat Lahir", v(s.tl)],
    ["Tanggal Lahir", v(s.tgl)],
    ["Jenis Kelamin", v(jk)],
    ["Agama", v(s.agama)],
    ["Anak Ke", v(s.anak)],
    ["Alamat Peserta Didik", v(s.alamat)],
    ["Telepon", v(s.tel)],
    ["Diterima di sekolah ini", null],
    ["di Kelas", v(s.dk)],
    ["pada tanggal", v(s.dtg)],
    ["sebagai", "Peserta Didik"],
    ["Nama Orang Tua", null],
    ["a. Ayah", v(s.ayah)],
    ["b. Ibu", v(s.ibu)],
    ["Pekerjaan Orang Tua", null],
    ["a. Ayah", v(s.kayah)],
    ["b. Ibu", v(s.kibu)],
    ["Nama Wali Peserta Didik", v(s.wali)],
    ["Pekerjaan Wali Peserta Didik", v(s.kwali)],
  ];
  return `<div class="pg ks">${wm()}<h2 class="kt">KETERANGAN DIRI TENTANG PESERTA DIDIK</h2><table class="k2">${r.map(([k, x]) => (x === null ? `<tr><td colspan="3">${k}</td></tr>` : `<tr><td>${k}</td><td>:</td><td>${x}</td></tr>`)).join("")}</table><div class="sg2"><div class="foto">PAS<br>3X4</div><div>${esc(c.tempat)}, ${esc(g)}<br>Kepala Sekolah,<br><br><br><br><br>${esc(c.kepala)}<br>NIP: ${esc(c.nipk || "-")}</div></div></div>`;
};
const CG =
  '<colgroup><col style="width:9mm"><col style="width:50mm"><col style="width:13mm"><col style="width:16mm"><col></colgroup>';
const rap = (s) => {
  const c = S.sch,
    d = D(),
    m = M(),
    z = ns(s),
    kl = c.kelas + track;
  let n = 0;
  const rw = (g) =>
    m[g]
      .filter((r) => r.n && !(r.sp && nv(s, r) === ""))
      .map((r) => {
        const x = nv(s, r),
          t = x === "" ? "" : +x >= m.batas ? r.a : r.b;
        return `<tr class="br"><td class="c b">${++n}</td><td class="mp">${esc(r.n)}</td><td class="c kn">${esc(r.kkm)}</td><td class="c kn">${esc(x)}</td><td class="ds">${esc(t)}</td></tr>`;
      });
  const gp = (t, a) =>
    a.length
      ? `<tr class="gr"><td colspan="5">${t}</td></tr>` + a.join("")
      : "";
  const u = rw("u"),
    p = rw("p");
  n = 0;
  const k = rw("k"),
    ek = m.e.map((e, i) => ({ ...e, p: z["e" + i] })).filter((e) => e.n && e.p);
  const eh = ek.length
    ? `<table class="t" style="margin-top:10mm"><colgroup><col style="width:9mm"><col style="width:50mm"><col style="width:28mm"><col></colgroup><thead><tr><th>No</th><th>Kegiatan Ekstrakurikuler</th><th>Predikat</th><th>Keterangan</th></tr></thead>${ek.map((e, i) => `<tr class="br"><td class="c b">${i + 1}</td><td class="mp">${esc(e.n)}</td><td class="pr">${esc(e.p)}</td><td class="ds">${esc(e.k)}</td></tr>`).join("")}</table>`
    : "";
  const ab = `<table class="ab"><tr><th colspan="5">Ketidakhadiran</th></tr>${[
    ["Izin", z.izin],
    ["Sakit", z.sakit],
    ["Alpa", z.alpa],
  ]
    .map(
      ([a, x], i) =>
        `<tr><td>${i + 1}</td><td>${a}</td><td>:</td><td style="text-align:center">${esc(x || "-")}</td><td>hari</td></tr>`,
    )
    .join("")}</table>`;
  const decision = legacyPrint() ? d.naik : s.decision;
  const nk = decision && c.sem === "Genap" ? `<div class="nk">${esc(decision)}</div>` : "";
  const tg = senior
    ? c.kelas === "XII"
      ? 6
      : 5
    : program === "b"
      ? c.kelas === "IX"
        ? 4
        : 3
      : ["I", "II", "III"].includes(c.kelas)
        ? 1
        : 2;
  return `<div class="pg">${wm()}<table class="hd"><tr><td style="width:40mm">Nama Satuan Pendidikan</td><td style="width:3mm">:</td><td>${esc(c.nama)}</td><td style="width:30mm">Kelas</td><td style="width:3mm">:</td><td style="width:30mm">${kl}</td></tr><tr><td>Alamat</td><td>:</td><td>${esc(c.a1)}</td><td>Semester</td><td>:</td><td>${esc(c.sem)}</td></tr><tr><td></td><td></td><td>${esc(c.ar)}</td><td>Tingkatan</td><td>:</td><td>${tg}</td></tr><tr><td></td><td></td><td></td><td>Tahun Pelajaran</td><td>:</td><td>${esc(d.tahun)}</td></tr></table><table class="hd"><tr><td style="width:40mm">Nama Peserta Didik</td><td style="width:3mm">:</td><td>${esc(s.nama)}</td></tr><tr><td>Nomor Induk/NISN</td><td>:</td><td>${v(s.nipd)} &nbsp;/&nbsp; ${v(s.nisn)}</td></tr></table><div class="sec">A. Lembar Isi Mata Pelajaran</div><table class="t">${CG}<thead><tr><th>No</th><th>Mata Pelajaran/Muatan Pemberdayaan dan Keterampilan</th><th>KKM</th><th>Nilai Akhir</th><th>Capaian Kompetensi</th></tr></thead>${gp("Kelompok Mata Pelajaran Umum", u)}${gp("Peminatan Ilmu-Ilmu " + (A ? "Alam" : "Sosial"), p)}</table></div>
<div class="pg">${wm()}${k.length ? `<table class="t">${CG}${gp("Kelompok Khusus", k)}</table>` : ""}${eh}<div class="sec">Catatan Wali Kelas</div><div class="cat">${esc(z.catatan || "")}</div>${ab}${nk}<div class="sg"><div><br>Orang Tua/Wali<br><span class="dot"></span></div><div>${esc(c.tempat)}, ${esc(m.tgl)}<br>Wali Kelas<br><br><br><br><u>${esc(d.wali)}</u><br>NIP : ${esc(d.nip || "-")}</div></div></div>`;
};
function fillWho() {
  const w = $("who"),
    cur = w.value,
    L = LS();
  w.innerHTML =
    '<option value="">Semua siswa (' +
    L.length +
    ")</option>" +
    L.map((s, i) => `<option value="${i}">${esc(s.nama)}</option>`).join("");
  w.value = cur || (L.length ? "0" : "");
}
function draw() {
  const L0 = LS(),
    w = $("who").value,
    L = w === "" ? L0 : [L0[+w]].filter(Boolean),
    ck = (i) => $(i).checked;
  $("sheet").innerHTML = L.length
    ? L.map((s) => {
        const i = L0.indexOf(s);
        return (
          (ck("c1") ? cov(s, i) : "") +
          (ck("c2") ? sek() : "") +
          (ck("c4") ? ktr(s) : "") +
          (ck("c3") ? rap(s) : "")
        );
      }).join("")
    : '<p class="mu">Belum ada siswa di kelas ini. Isi di tab Data Siswa &amp; Nilai.</p>';
}
function tab(n) {
  for (let i = 1; i < 4; i++) {
    $("t" + i).hidden = i != n;
    $("b" + i).classList.toggle("on", i == n);
  }
  if (n == 3) {
    $("who").value = "";
    fillWho();
    draw();
  }
  if (n == 2) lst();
}
function chg() {
  S.sch.kelas = $("kl").value;
  S.sch.sem = $("sm").value;
  save();
  setup();
  lst();
  if (!$("t3").hidden) {
    $("who").value = "";
    fillWho();
    draw();
  }
}
