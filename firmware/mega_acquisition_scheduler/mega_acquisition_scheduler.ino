// Transcribed verbatim from Appendix A of J. A. Carvalho Neto, "Sistema de iluminação de
// granjas controladas por lógica fuzzy", M.Sc. dissertation, FCA/Unesp, Botucatu, 2021.
// Not modified (comments and identifiers are in Portuguese, as in the original). Not re-tested
// on hardware for this release. See firmware/README.md for notes and known discrepancies.

const int ledPin =  LED_BUILTIN;
int ledState = LOW;             
int dia=8;
int hora=14;
int minuto=53;
int C=0;
int BT=10;
int BT5=9;
int BT3=8;
int BT2=7;
int ALT=0;
int Set_point=0;
float lux3;
unsigned long previousMillis = 0;        
unsigned long previousMillis_h = 0;  
unsigned long previousMillis_m = 0; 
int buttonState_12 = 0; 
int buttonState_5 = 0;
int buttonState_3 = 0;
int buttonState_2 = 0;
const long interval = 86400000;           
const long interval_h = 3600000;
const long interval_m =60000;
#include <Wire.h>
#include <BH1750.h>
#define N 10
int foto_res = 0;
int loop_read[N];
// programa do luximetro
BH1750 lightMeter(0x23);
int media;
int cont=0;
const int analogInPin = A0;  
const int analogOutPin = 9; 
int sensorValue = 0;        
int outputValue = 0;  
void setup(){
  pinMode(BT, INPUT);
  pinMode(BT5, INPUT);
  pinMode(BT3, INPUT);
  pinMode(BT2, INPUT);
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  Wire.begin();
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
  }
  else {
  }
}
void loop() 
{ 
buttonState_12=digitalRead(BT);
buttonState_5=digitalRead(BT5);
buttonState_3=digitalRead(BT3);
buttonState_2=digitalRead(BT2);
if (buttonState_12==1)
{
ALT=1;  
}
if (buttonState_5==1)
{
ALT=5;  
dia=5;
}
if (buttonState_3==1)
{
ALT=3;  
dia=3;
}
if (buttonState_2==1)
{
ALT=2;  
dia=2;
}
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis_m >= interval_m) 
    {
      minuto=minuto+1;
      if(minuto>=60)// para zerar o minuto quando chegar a 60 e acrescentar em hora
      {
        minuto=0;
        hora=hora+1; 
        }
      if(hora>=24)
      {
        if(ALT!=5&&ALT!=3&&ALT!=2)
          { 
          dia=dia+1;
          }
        if(ALT==5||ALT==3||ALT==2)
          { 
          dia=dia-1;
          }  
        hora=0;
       }
      previousMillis_m = currentMillis;
if (dia==0)
 {
 // Serial.println("   ");  
      //Serial.println("25 Lux, 0 hora de escuro");
 }
 if (dia>=1&&dia<7&&ALT==0)
 {
      //Serial.println("   ");  
      //Serial.println("25 Lux, 1 hora de escuro");
      if (hora>=23)
      {
        //Serial.println("Setpoint=0 das 23:00 as 0:00");
        Set_point=1;   
        }
        if (hora>=0&&hora<23)
        {
          //Serial.println("Setpoint=25 lux das 0:00 as 23:00");
           Set_point=33;         
          }
  } 

  if((dia>=7||ALT==1)&&dia<22)
  {
    ALT=1;
    //Serial.println(" ");
    //Serial.println("10 lux, 10 horas de escuro");   
 if (hora>=20)
      {
        //Serial.println("Setpoint=0 das 20:00 as 6:00");
        Set_point=1;
        }
        if (hora>=0 && hora<6)
      {
        //Serial.println("Setpoint=0 das 20:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6 && hora<20)
        {
          //Serial.println("Setpoint=10 lux das 06:00 as 20:00");
          Set_point=10;
          }  
    }
 if(dia>=22&&dia<28)
  {
    ALT=1;
    //Serial.println(" ");
    //Serial.println("10 lux");
    //Serial.println("9 horas de escuro");
if (hora>=21)
      {
        //Serial.println("Setpoint=0 das 21:00 as 6:00");
        Set_point=1;
        }
        if (hora>=0 && hora<6)
      {
        //Serial.println("Setpoint=0 das 21:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6 && hora<21)
        {
          //Serial.println("Setpoint=10 lux das 06:00 as 21:00");
          Set_point=10;
          }
    }
if(dia>=28&&dia<35)
  {
    ALT=1;
    //Serial.println(" ");
    //Serial.println("10 lux, 8 horas de escuro"); 
  if (hora>=22)
      {
        //Serial.println("Setpoint=0 das 22:00 as 6:00");
        Set_point=1;
        }
        if (hora>=0 && hora<6)
      {
       // Serial.println("Setpoint=0 das 22:00 as 6:00");
       Set_point=1;
        }
        if (hora>=6 && hora<22)
        {
          //Serial.println("Setpoint=10 lux das 06:00 as 22:00");
          Set_point=10;
          }
    }
if(dia>=35 && dia<42)
  {
    ALT=1;
    //Serial.println(" ");
    //Serial.println("10 lux, 7 horas de escuro");
 if (hora>=23)
      {
        //Serial.println("Setpoint=0 das 23:00 as 6:00");
        Set_point=1;
        }
        if (hora>=0 && hora<6)
      {
        //Serial.println("Setpoint=0 das 23:00 as 6:00");
        Set_point=1;
        }

        if (hora>=6 && hora<23)
        {
          //Serial.println("Setpoint=10 lux das 06:00 as 23:00");
          Set_point=10;
          }
   }
if(dia>=42 && dia<49)
  {
    ALT=1;
    //Serial.println(" ");
    //Serial.println("10 lux, 6 horas de escuro");
        if (hora>=0 && hora<6)
      {
        //Serial.println("Setpoint=0 das 0:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6)
        {
          //Serial.println("Setpoint=10 lux das 6:00 as 0:00");
          Set_point=10;
          }
   }
if(ALT==5&&dia==5)
  {
    //Serial.println(" ");
    //Serial.println("10 lux, 5 horas de escuro");
  if (hora>=1 && hora<6)
      {
        //Serial.println("Setpoint=0 das 1:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6 || hora<1)
        {
          //Serial.println("Setpoint=10 lux das 6:00 as 1:00");
          Set_point=10;
          }
   }
if(ALT==5&&dia==4)
  {
    
    //Serial.println(" ");
    //Serial.println("10 lux, 4 horas de escuro");
    if (hora>=2 && hora<6)
      {
        //Serial.println("Setpoint=0 das 2:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6 || hora<2)
        {
          //Serial.println("Setpoint=10 lux das 6:00 as 2:00");
          Set_point=10;
          }    
   }
if((ALT==5||ALT==3)&&dia==3)
  {
    //Serial.println(" ");
   // Serial.println("10 lux, 3 horas de escuro");
    if (hora>=3 && hora<6)
      {
        //Serial.println("Setpoint=0 das 3:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6 || hora<3)
        {
          //Serial.println("Setpoint=10 lux das 6:00 as 3:00");
          Set_point=10;
          } 
   }
if((ALT==5||ALT==3||ALT==2)&&dia==2)
  {
    //Serial.println(" ");
    //Serial.println("10 lux, 2 horas de escuro");
    if (hora>=4 && hora<6)
      {
        //Serial.println("Setpoint=0 das 4:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6 || hora<4)
        {
          //Serial.println("Setpoint=10 lux das 6:00 as 4:00");
          Set_point=10;
          }
   }
if((ALT==5||ALT==3||ALT==2)&&dia==1)
   {
    //Serial.println(" ");
    //Serial.println("10 lux, 2 horas de escuro");
    if (hora>=5 && hora<6)
      {
        //Serial.println("Setpoint=0 das 5:00 as 6:00");
        Set_point=1;
        }
        if (hora>=6 || hora<5)
        {
          //Serial.println("Setpoint=10 lux das 6:00 as 5:00");
          Set_point=10;
          }
   } 
  }
if(Serial.available()>0)
  {
        char txt=Serial.read();// converte a leitura por txt
        txt=txt;
      if (txt=='D'||txt=='d')
      {  
      Serial.println("   ");
      Serial.print("Dia ");
      Serial.print(dia);
      Serial.print("       Horario ");
      Serial.print(hora);
      Serial.print(":");  
    if (minuto<10)//para colocar o "0" a esquerda de números menores que 10
    {
      Serial.print("0");
    }
          Serial.println(minuto);
      Serial.print("Setpoint");
      Serial.print("     ");
      Serial.println(Set_point);
      }
    }
  {// inico do BH1750*********************
  uint16_t lux = lightMeter.readLightLevel();
  //Serial.print("Light: ");
  float read_res = lux;
for (int i = N-1; i > 0; i--)
{
loop_read[i] = loop_read[i-1];
}
loop_read[0] = read_res;
long soma = 0;
for (int i = 0; i < N; i++)
{
soma = soma + loop_read[i];
}
media = soma/N;
int lux2=0.7777*lux-0.4562;//Equação obtida pelo Excel//lux sem média móvel
  if (Set_point==0 || Set_point==1)
  {
    lux3=100;
  }
  else
  {
  lux3=(lux2*100/Set_point)-100; //SETPOINT  em 25 Lux
  }
 //Serial.println(lux_2);
//Serial.print(" ");
  //Serial.println( lux3 );
  //Serial.println( lux2 );
  //Serial.println( media );
 // Serial.println(" lx");
  delay(200);
  if(Serial.available()>0)
  {   
        char txt=Serial.read();// converte a leitura por txt
        txt=txt;
        if (txt=='C' || txt=='c')// exclusivos para testes
        {
        Serial.println("**********************************************");
        Serial.println("Sinal Original");
          Serial.println(lux);
          Serial.println(" ");
          Serial.println("Sinal Filtrado");
          Serial.println(media);
          Serial.println(" ");
          Serial.println("Sinal da equação");
          Serial.println(lux2);
          Serial.println(" ");
        }
if (txt=='B' || txt=='b')// exclusivo para testes
        {    
          Serial.println(lux2);
                }
if (txt=='D' || txt=='d')// exclusivos para testes
        {
        Serial.println("**********************************************");
        Serial.println("   ");  
        Serial.print("Dia ");
        Serial.print(dia);
        Serial.print("   ");
        Serial.print(hora);
        Serial.print(":");
        if (minuto<10)
        {
        Serial.print("0");
        }
        Serial.println(minuto);   
        Serial.print("Setpoint");
        Serial.print("   ");
        Serial.println(Set_point);        
        }
               if (txt=='A' || txt=='a')
        {
              if (lux3>=100)
        {
          lux3=100;
        }
        if (lux3<=-100)
        {
          lux3=-100;
        }
// mudança
if (Set_point==33)
{
        if (lux3>=-5 && lux3<=5)
        {
          lux3=0;
          }
}
if (Set_point==10)
{         
if (lux3>=-9 && lux3<=9)
        {
          lux3=0;
          }
}          
 //Serial.println( "***********************************" ); 
         //Serial.println( "valor original" ); 
       //Serial.println( lux);//valor original
       //Serial.println( " " );
        //Serial.println( "correcaum e media" );
       //Serial.println( media ); //valor map
       //Serial.println( " " );
         //Serial.println( "valor da equação" );
       //Serial.println( lux2 ); //valor map
       //Serial.println( " " );
       //Serial.println( "porcentagem para 25 Lux");    
      Serial.println( lux3 ); //envia porcentagem do erro para 25 Lux
      //Serial.println( " " );
      //Serial.println( "porcentagem para 10 Lux");    
      //Serial.println( lux4 ); //envia porcentagem do erro para 25 Lux
   }
}
  }//final do BH1750*************************************************
   }//Fechamento do loop
