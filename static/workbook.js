const issuedId = Number(document.body.dataset.issue);
const endpoint = issuedId
  ? "/api/issued/" + issuedId
  : "/api/book/" + program + "/" + year;
let revision = 0;
let dirty = false;
let timer;
let pending;

function statusMessage(message, problem = false) {
  $("status").textContent = message;
  $("status").parentElement.classList.toggle("problem", problem);
}

async function post(payload) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": document.body.dataset.csrf,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok)
    throw new Error(
      {
        401: "Sesi berakhir. Masuk kembali untuk melanjutkan.",
        403: "Sesi telah berubah. Buka ulang buku melalui ruang guru.",
        409: "Buku berubah di tab lain. Salin perubahan Anda sebelum memuat ulang.",
        413: "Buku melebihi batas 4 MB. Kurangi ukuran logo atau jumlah data.",
        422: "Periksa data. Nilai dan KKM harus 0–100, jumlah absen bilangan bulat, dan nama mapel harus unik.",
      }[response.status] || "Server tidak dapat menyimpan perubahan.",
    );
  return response.json();
}

function save() {
  if (issuedId) return;
  for (const group of Object.values(S.c)) {
    while (group.st.length && emp(group.st.at(-1))) group.st.pop();
  }
  dirty = true;
  statusMessage("Ada perubahan yang belum tersimpan.");
  clearTimeout(timer);
  timer = setTimeout(flush, 500);
}

async function flush() {
  clearTimeout(timer);
  if (pending) return pending;
  pending = (async () => {
    try {
      while (dirty) {
        dirty = false;
        statusMessage("Menyimpan…");
        revision = (await post({ rev: revision, state: S })).rev;
      }
      $("retry").hidden = true;
      statusMessage("Tersimpan · revisi " + revision);
      return true;
    } catch (error) {
      dirty = true;
      $("retry").hidden = false;
      statusMessage("Belum tersimpan. " + error.message, true);
      return false;
    }
  })();
  try {
    return await pending;
  } finally {
    pending = null;
  }
}

function review() {
  const subjects = allM().filter((r) => !r.sp);
  const group = D();
  const missing = group.st.filter(
    (s) => !s.nama?.trim() || subjects.some((r) => nv(s, r) === ""),
  );
  const gaps = [];
  if (!group.st.length) gaps.push("daftar siswa");
  if (!group.wali.trim()) gaps.push("nama wali kelas");
  if (!M().tgl.trim()) gaps.push("tanggal rapor");
  if (!subjects.length) gaps.push("mata pelajaran");
  if (missing.length)
    gaps.push("nama atau nilai wajib untuk " + missing.length + " siswa");
  $("check").textContent = issuedId
    ? "Arsip #" + issuedId + " · Kelas " + S.sch.kelas + " · " + S.sch.sem
    : gaps.length
      ? "Lengkapi " + gaps.join(", ") + " sebelum menerbitkan arsip."
      : group.st.length +
        " siswa siap diterbitkan untuk semester " +
        S.sch.sem +
        ".";
  const list = $("missing");
  list.replaceChildren();
  group.st.forEach((student, index) => {
    const fields = subjects
      .filter((r) => nv(student, r) === "")
      .map((r) => r.n);
    if (!student.nama?.trim()) fields.unshift("Nama siswa");
    if (fields.length) {
      const line = document.createElement("li");
      line.textContent =
        (student.nama || "Baris " + (index + 1)) + " — " + fields.join(", ");
      list.append(line);
    }
  });
  $("details").hidden = issuedId || list.childElementCount === 0;
  $("issue").disabled = !!gaps.length;
  stamp();
}

function stamp() {
  for (const page of $("sheet").children) {
    page.dataset.stamp = issuedId
      ? "Rapor Digital · Arsip #" + issuedId
      : "DRAF · Belum diterbitkan";
  }
}

async function issue() {
  if (
    !confirm(
      "Terbitkan salinan tetap untuk seluruh siswa kelas " +
        S.sch.kelas +
        ", semester " +
        S.sch.sem +
        "?",
    )
  )
    return;
  $("work").inert = true;
  try {
    if (await flush()) {
      const result = await post({ action: "issue", rev: revision });
      location.assign(result.url);
    }
  } catch (error) {
    statusMessage(error.message, true);
  } finally {
    $("work").inert = false;
  }
}

document.addEventListener("click", (event) => {
  const action = event.target.closest("button")?.dataset.action;
  if (action === "print") {
    window.print();
    return;
  }
  if (issuedId) return;
  if (action?.startsWith("tab")) {
    tab(Number(action.slice(3)));
    if (action === "tab3") review();
  }
  if (action === "more") more();
  if (action === "clr") clr();
  if (action === "copy") cpm();
  if (action === "remove-logo") {
    S.logo = "";
    save();
    setup();
  }
});
document.addEventListener("change", (event) => {
  const action = event.target.dataset.action;
  if (action === "chg" && !issuedId) {
    chg();
    if (!$("t3").hidden) review();
  }
  if (action === "logo" && !issuedId) logo(event.target);
  if (action === "draw") {
    draw();
    stamp();
  }
});
window.addEventListener("beforeunload", (event) => {
  if (dirty || pending) {
    event.preventDefault();
    event.returnValue = "";
  }
});
window.addEventListener("pageshow", (event) => {
  if (event.persisted) location.reload();
});
$("retry").addEventListener("click", flush);
$("issue").addEventListener("click", issue);

async function openBook() {
  try {
    const response = await fetch(endpoint);
    if (response.status === 401) {
      location.replace("/login");
      return;
    }
    if (!response.ok) throw new Error();
    const result = await response.json();
    revision = result.rev;
    S = result.state || def();
    $("kl").innerHTML = KL.map((o) => opt(o, S.sch.kelas)).join("");
    $("sm").innerHTML = ["Ganjil", "Genap"]
      .map((o) => opt(o, S.sch.sem))
      .join("");
    if (issuedId) {
      $("classes").hidden = true;
      document.querySelector(".tabs").hidden = true;
      $("issue").hidden = true;
      tab(3);
      review();
    } else {
      setup();
      tab(revision ? 2 : 1);
    }
    statusMessage(
      issuedId
        ? "Arsip terbit · hanya baca"
        : revision
          ? "Tersimpan · revisi " + revision
          : "Buku baru · mulai dengan pengaturan kelas.",
    );
    $("loading").hidden = true;
    $("work").hidden = false;
  } catch {
    $("loading").textContent =
      "Buku tidak dapat dibuka. Muat ulang atau hubungi pengelola.";
  }
}
openBook();

$("leave").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("work").inert = true;
  try {
    if ((!dirty && !pending) || (await flush())) $("leave").submit();
  } finally {
    $("work").inert = false;
  }
});
