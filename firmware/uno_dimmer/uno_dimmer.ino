// Transcribed verbatim from Appendix B of J. A. Carvalho Neto, "Sistema de iluminação de
// granjas controladas por lógica fuzzy", M.Sc. dissertation, FCA/Unesp, Botucatu, 2021.
// Not modified (comments and identifiers are in Portuguese, as in the original). Not re-tested
// on hardware for this release. See firmware/README.md for notes and known discrepancies.

int PIN_3 = 3;
volatile float POT =100;
volatile float POT2=0;
volatile float tv=0;
int BOT_A0 = A0, BOT_A3 = A3;
void setup()
{
  Serial.begin(9600);
pinMode(PIN_3, OUTPUT);
attachInterrupt(0, Passagem_por_ZERO, RISING);
pinMode(BOT_A0, INPUT);
pinMode(BOT_A3, INPUT);
digitalWrite(BOT_A0, LOW);
digitalWrite(BOT_A3, LOW);
}
void loop()
{
if(Serial.available()>0)
  {   
    POT2=Serial.parseFloat();
    if (POT2>15)//limitação de erro
      {
      POT2=0;
      }    
      if (POT2<-15)
      {
      POT2=0;
      }
      POT=POT+POT2;
    if (POT>=100)//limitação de potência
      {
      POT=100;
      }     
     if (POT<=0)//limitação de potência
      {
      POT=0;
      }
//Serial.println(POT);
volatile float angulo=(83.33 * (100 - POT))*180/8333;
//Serial.println(angulo);
 volatile float POTtime_2 = (83.33 * (100 - POT))/1000;
volatile float Vef=296.98*sqrt(0.5-(angulo/360)+(sin(2*angulo)/(4*PI)));
//volatile float seno=sqrt(0.5-(angulo/360)+(sin(2*angulo)/(4*PI)));
/*Serial.println("***********************************");
Serial.println("Tempo para disparo");
Serial.println(POTtime_2);
Serial.println("   ");
Serial.println("Angulo");
Serial.println(angulo);
Serial.println("   ");
Serial.println("Tensao eficaz");
Serial.println(Vef);
Serial.println("   ");
Serial.println("   ");*/
Serial.println(angulo);
//Serial.println(POT);
  }
}//******************************** FIM DO LOOP
//**********************************INTERRUPÇÃO
void Passagem_por_ZERO()
{
float POTtime = (83.33 * (100 - POT));
if (POTtime <= 820)
{
digitalWrite(PIN_3, HIGH);
}
else if (POTtime >= 8000)
{
digitalWrite(PIN_3, LOW);
}
else if ((POTtime > 820) && (POTtime < 8000))
{
delayMicroseconds(POTtime);
digitalWrite(PIN_3, HIGH);
delayMicroseconds(8);
digitalWrite(PIN_3, LOW);
}
}// **********************************FIM da INTERRUPÇÃO
