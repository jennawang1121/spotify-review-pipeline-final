import {createServer} from "node:http";
import {DatabaseSync} from "node:sqlite";
import {mkdirSync,readFileSync,readdirSync} from "node:fs";
import {pathToFileURL} from "node:url";
import path from "node:path";
mkdirSync(".sites-runtime",{recursive:true});
const db=new DatabaseSync(".sites-runtime/preview.sqlite");
// Run local migrations once, preserving real persisted data across previews.
db.exec("CREATE TABLE IF NOT EXISTS _preview_migrations(name TEXT PRIMARY KEY)");
for(const file of readdirSync("drizzle").filter(f=>f.endsWith(".sql")).sort()){
  if(db.prepare("SELECT name FROM _preview_migrations WHERE name=?").get(file))continue;
  db.exec(readFileSync(path.join("drizzle",file),"utf8"));db.prepare("INSERT INTO _preview_migrations VALUES(?)").run(file);
}
const adapter={prepare(sql){let params=[];return {bind(...values){params=values;return this;},async first(){return db.prepare(sql).get(...params)??null;},async all(){return {results:db.prepare(sql).all(...params)};},async run(){db.prepare(sql).run(...params);return {success:true};}};},async batch(statements){db.exec("BEGIN");try{for(const s of statements)await s.run();db.exec("COMMIT");return [];}catch(e){db.exec("ROLLBACK");throw e;}}};
const worker=(await import(pathToFileURL(path.resolve("worker/index.js")))).default;
const server=createServer(async(req,res)=>{try{const request=new Request("http://127.0.0.1:8787"+req.url,{method:req.method});const response=await worker.fetch(request,{DB:adapter});res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()));}catch(error){console.error(error);res.writeHead(500);res.end("Preview failed");}});
server.listen(8787,"127.0.0.1",()=>console.log("Local: http://127.0.0.1:8787"));
process.on("SIGTERM",()=>server.close(()=>{db.close();process.exit(0);}));
