import {readFile,writeFile} from "node:fs/promises";
const root=new URL("../",import.meta.url);
const files=await Promise.all(["data/seed.json","src/index.html","src/client.js","src/style.css","src/backend.js"].map(p=>readFile(new URL(p,root),"utf8")));
const seed=JSON.parse(files[0]);
let backend=files[4];
if(process.env.SITES_PRIVATE_IMPORT === "1"){
  const importer=await readFile(new URL("scripts/private-import-handler.js",root),"utf8");
  backend=importer+backend.replace('    if(url.pathname.startsWith("/api/")){','    if(url.pathname==="/api/import")return importRows(request,env);\n    if(url.pathname.startsWith("/api/")){');
}
if(!seed.external_count && seed.reviews.length!==seed.summary.source_rows)throw new Error("Seed coverage mismatch");
await writeFile(new URL("worker/index.js",root),"// Built from src/ and verified saved pipeline evidence. No model calls.\nconst SEED="+JSON.stringify(seed)+";\nconst HTML="+JSON.stringify(files[1])+";\nconst CLIENT="+JSON.stringify(files[2])+";\nconst CSS="+JSON.stringify(files[3])+";\n"+backend);
