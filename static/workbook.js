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
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.error || (
      {
        401: "Sesi berakhir. Masuk kembali untuk melanjutkan.",
        403: "Sesi telah berubah. Buka ulang buku melalui ruang guru.",
        409: "Buku berubah di tab lain. Salin perubahan Anda sebelum memuat ulang.",
        413: "Buku melebihi batas 4 MB. Kurangi ukuran logo atau jumlah data.",
        422: "Periksa data. Nilai dan KKM harus 0–100, jumlah absen bilangan bulat, dan nama mapel harus unik.",
      }[response.status] || "Server tidak dapat menyimpan perubahan."));
  }
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
  showRecap();
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
      $("historyBox").hidden = true;
      $("recapBox").hidden = true;
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

function showRecap() {
  if (issuedId) return;
  const genap = S.sch.sem === "Genap";
  $("decisionHead").hidden = !genap;
  $("rollover").hidden = !genap || year >= 2100;
  const subjects = allM();
  $("recap").replaceChildren();
  for (const student of LS()) {
    const scores = subjects.map(r => nv(student,r)).filter(v => v !== "");
    const average = scores.length && scores.every(v => Number.isFinite(Number(v)) && Number(v) >= 0 && Number(v) <= 100)
      ? scores.reduce((sum,v) => sum+Number(v),0)/scores.length : null;
    const row = $("recap").insertRow();
    for (const value of [student.nama, scores.length, average === null ? "—" : average.toLocaleString("id-ID",{maximumFractionDigits:2})])
      row.insertCell().textContent = value;
    if (!genap) continue;
    const select = document.createElement("select");
    select.setAttribute("aria-label","Keputusan untuk " + student.nama);
    for (const option of ["","Tinggal kelas", S.sch.kelas === KL.at(-1) ? "Lulus" : "Naik kelas"])
      select.add(new Option(option || "Belum diputuskan",option));
    select.value = student.decision || "";
    select.addEventListener("change", () => {
      student.decision = select.value;
      save(); draw(); stamp();
    });
    row.insertCell().append(select);
  }
}

async function bookAction(run) {
  $("work").inert = true;
  try {
    if ((!dirty && !pending) || await flush()) await run();
  } catch (error) {
    statusMessage(error.message,true);
  } finally {
    $("work").inert = false;
  }
}

$("rollover").onclick = () => {
  const preview = [];
  let continuing = 0;
  for (const grade of KL) {
    const students = S.c[grade].st;
    if (!students.length) continue;
    if (students.some(s => !s.nama?.trim() || !s.decision))
      return alert("Lengkapi nama dan keputusan setiap siswa kelas " + grade + " pada semester Genap.");
    const totals = ["Naik kelas","Tinggal kelas","Lulus"].map(label => {
      const count = students.filter(s => s.decision === label).length;
      if (label !== "Lulus") continuing += count;
      return count ? count+" "+label : "";
    }).filter(Boolean);
    preview.push("Kelas "+grade+" — "+totals.join(", "));
  }
  if (!continuing) return alert("Tidak ada siswa yang perlu disalin.");
  if (confirm("Buat buku "+(year+1)+"/"+(year+2)+" dengan nilai kosong?\n"+preview.join("\n")))
    bookAction(async () => location.assign((await post({rev:revision,action:"rollover"})).url));
};
$("historyLoad").onclick = () => bookAction(async () => {
  const {versions} = await post({rev:revision,action:"history"});
  $("versions").replaceChildren(...versions.map(v => new Option("Revisi "+v,v)));
  $("historyChoice").hidden = $("restore").hidden = !versions.length;
  $("historyInfo").textContent = versions.length ? "" : "Belum ada revisi terdahulu.";
});
$("restore").onclick = () => {
  const version = Number($("versions").value);
  if (confirm("Pulihkan seluruh buku program ini dari revisi "+version+" sebagai draf baru?"))
    bookAction(async () => {
      await post({action:"restore",rev:revision,version});
      location.reload();
    });
};
