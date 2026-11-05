use <det.scad>
A=""; B="";
module O(n){
 if(n=="TRAY") TRAY(); if(n=="GB") GB(); if(n=="CR") CR(); if(n=="SCR") SCR(); if(n=="MOT") MOT2();
 if(n=="TIES") TIES(); if(n=="CPL") CPL(); if(n=="ENC") ENC(); if(n=="MAG") MAG(); if(n=="BRK") BRK();
 if(n=="HALL") HALL(); if(n=="TS") TS(); if(n=="BSCR") BSCR(); }
intersection(){ O(A); O(B); }
