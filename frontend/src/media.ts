/** Resolve only backend media paths; never infer measurements from media metadata. */
export function mediaUrl(path:string|null|undefined,apiBase=''):string|undefined {
  if(!path)return undefined;
  if(!path.startsWith('/media/'))return undefined;
  if(!apiBase)return path;
  try {const base=new URL(apiBase);if(!['http:','https:'].includes(base.protocol))return undefined;return new URL(path,base.origin).href}catch{return undefined}
}
