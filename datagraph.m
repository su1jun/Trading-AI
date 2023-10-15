data=readmatrix('KRW-CELO_t.csv'); 

len = 386;
x=1:len;
y=data(2:len+1,3).';
y2=data(2:len+1,4).';
z=data(2:len+1,8).';
z1=data(2:len+1,10).';
% z2=data(2:len+1,16).';

figure(1);
subplot(211);
plot(x,y)
grid on;
xlabel('y');
ylabel('x');
title('Data')
hold on;

% plot(x,y2)
hold on;

subplot(212);
plot(x,z - z1)
grid on;
xlabel('z');
ylabel('x');
title('Data')
hold on;

% plot(x,z1, 'or')
hold on;

% plot(x,z2, 'ob')
hold on;
