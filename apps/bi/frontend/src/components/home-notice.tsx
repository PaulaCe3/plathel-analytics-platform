"use client";
import { useEffect, useState } from "react";
import { Toast } from "@/components/ui/primitives";
import { t } from "@/lib/i18n";
export function HomeNotice({deleted,expired}:{deleted:boolean;expired:boolean}) {
 const [visible,setVisible]=useState(deleted || expired);
 useEffect(()=>{if(!deleted || expired) return; const timer=setTimeout(()=>{setVisible(false);const url=new URL(window.location.href);url.searchParams.delete("deleted");window.history.replaceState(window.history.state,"",url.pathname+url.search+url.hash);},6000);return ()=>clearTimeout(timer);},[deleted,expired]);
 return <Toast tone={expired ? "info" : "success"}>{visible ? t(expired ? "session.expired" : "home.deleted") : null}</Toast>;
}
