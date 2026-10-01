// Presets use the last available date, so historical datasets remain useful.
export function datePreset(preset:string, minimum:string, maximum:string):string[]{
 const end=new Date(`${maximum.slice(0,10)}T00:00:00Z`);const start=new Date(end);
 if(preset==="30d")start.setUTCDate(start.getUTCDate()-29);
 else if(preset==="year")start.setUTCMonth(0,1);
 else {const months=Number(preset);if(![3,6,12].includes(months))return [minimum,maximum];start.setUTCDate(1);start.setUTCMonth(start.getUTCMonth()-months+1);}
 const from=start.toISOString().slice(0,10);return [from<minimum?minimum:from,maximum];
}
