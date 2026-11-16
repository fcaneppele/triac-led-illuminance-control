% Transcribed verbatim from Appendix C of J. A. Carvalho Neto, "Sistema de iluminação de
% granjas controladas por lógica fuzzy", M.Sc. dissertation, FCA/Unesp, Botucatu, 2021.
% Not modified (comments and identifiers are in Portuguese, as in the original). Not re-tested
% on hardware for this release. See firmware/README.md for notes and known discrepancies.

clc, clear all, close all,
delete(instrfind({'Port'},{'COM3'}))
delete(instrfind({'Port'},{'COM4'}))
ard=serial('COM4','BAUD', 9600);%UNO
ard2=serial('COM3','BAUD', 9600);%MEGA
fopen(ard);
fopen(ard2);
pause(1)
fprintf(ard,'0');%potência do triac
 stp=25;
 disp ('Inicio do programa');
%%power=70;
pause(4);
passo = 0.01;
ind_s=0;
i=1;
j=1;
z=1;
w=1;
%data=1;
%data_vo=1;
data_stp=1;
 while ind_s<=150;
 format bank;
%% inserção via teclado     
%ind_s=input('Informe o erro da leitura: ', 's');
%e0=str2double(ind_s);
 %% comunicação Arduino
 fprintf(ard2,'A');
%pause(1);
%fprintf(ard2,'A');%% para dar tempo do arduino enviar o valor correto (2
%%ciclos)
%disp('valor enviado do arduino:');
ind_s=fscanf(ard2,'%f');
disp('Valor corrigido');
disp(ind_s);
data(i)=ind_s;
subplot (3,1,2), plot(data,'b','LineWidth',3);
set(gca,'FontSize',12), %legend('LB','LM','LA')
xlabel('Ciclos'), ylabel('PE')
grid on;
i=i+1;
disp('erro');
%e0=(ind_s*100/stp)-100;%% fazer o calculo do erro
e0=ind_s;% erro já enviado pelo arduino
if e0>100
    e0=100;
end  
if e0<-100
    e0=-100;
end 
 %e0=30;
%% Erro de posição
e= -100:passo:100;
EB= trapmf(e,[-100 -100 -50 0]);
EM=trimf(e,[-50 0 50]);
EA=trapmf(e,[0 50 100 100]);
%% figura fuzzy
%subplot (3,1,1), plot(e,EB,'b',e,EM,'y',e,EA,'r','LineWidth',3)
%set(gca,'FontSize',12), legend('LB','LM','LA')
%xlabel('ERRO %'), ylabel('\mu(E)')
%grid on;
%axis([-50 50 0 1.1])%define o tamanho dos eixos x e y
%% Ação de controle
passo=0.1;
v=-15:passo:15;
SB= trapmf(v,[-15 -15 -9 0]);
SM=trimf(v,[-9 0 9]);
SA=trapmf(v,[0 9 15 15]);
%% figura fuzzy
%subplot (3,1,2), plot(v,SB,'b',v,SM,'y',v,SA,'r','LineWidth',3)
%set(gca,'FontSize',12), legend('TB','TM','TA')
%xlabel('Correção %'), ylabel('\mu(S)')
%axis([-15 15 0 1.1])
%grid on;
%% Leitura do erro
n=find(e==e0);
%subplot(3,1,1), hold on, plot(e0,EB(n),'*',e0,EM(n),'*',e0,EA(n),'*','LineWidth',3), hold off
%% Fuzzificar e Inferência de Mamdani
 %%if ind_s <= -11 ||  ind_s>=11
B1=min(SB,EA(n));
B2=min(SM,EM(n));
B3=min(SA,EB(n));
B=max(B1,max(B2,B3));
%% figura fuzzy
%subplot(3,1,3),plot(v,B,'LineWidth',3)
%set(gca,'FontSize',12), legend('V')
%axis([-15 15 0 1.1])
%grid on;  
%% desfuzzificação centro de área
vo=defuzz(v,B,'centroid');
%% figura fuzzy
%hold on, plot(vo*ones(1,3),[0 0.5 2], 'r', 'LineWidth',3)
%disp('Centro de área:');
%title(vo);
%xlabel('Saída Correção'), ylabel('\mu(S)')
%% Saída do sinal
if e0==0
    vo=0;
end
disp(vo);
if vo<=2
fprintf(ard,'%f',vo);%para enviar o numero float para o arduino uno    
end
if vo>2
fprintf(ard,'%d',vo);%para enviar o numero int para o arduino uno
end
 data_vo(j)=vo;
subplot (3,1,3), plot(data_vo,'b', 'LineWidth',3);
set(gca,'FontSize',12), %legend('LB','LM','LA')
xlabel('Ciclos'), ylabel('CE')
grid on;
 j=j+1; 
 fprintf(ard2,'B');
%pause(1);
%fprintf(ard2,'A');%% para dar tempo do arduino enviar o valor correto (2
%%ciclos)
%disp('valor enviado do arduino:');
ind_x=fscanf(ard2,'%f');
                                           %ind_x=10; 
disp('Valor Lux');
disp(ind_x);
data_x(z)=ind_x;
subplot (3,1,1), plot(data_x,'b', 'LineWidth',3);
set(gca,'FontSize',12), %legend('LB','LM','LA')
xlabel('Ciclos'), ylabel('Lux %')
grid on;
 z=z+1; 
Vef_x=fscanf(ard,'%f');
disp('power');
disp(Vef_x);
%data_w(w)=Vef_x;
%subplot (4,1,4), plot(data_w,'b', 'LineWidth',3);
%set(gca,'FontSize',12), %legend('LB','LM','LA')
%xlabel('Ciclos'), ylabel('Vef')
%grid on;
 %w=w+1;
pause(3);
%% Envio de resultados para o arduino através da porta serial
 end
 delete(instrfind({'Port'},{'COM3'}))
delete(instrfind({'Port'},{'COM4'}))
