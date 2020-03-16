clear
clc
close all
figure 

dialogBox = uicontrol('Style', 'PushButton', 'String', 'Break','Callback', 'delete(gcbf)');

PORT = 1002;
udp_sock = udp('localhost',PORT, 'localport', PORT);
fopen (udp_sock);

display_arr = ones ([6,1500]);

A = zeros([6,1]);
prv_A = 0;

x = display_arr(6,:);
TP9 = display_arr(1,:);
AF7 = display_arr(2,:);
AF8 = display_arr(3,:);
TP10 = display_arr(4,:);
RAUX = display_arr(5,:);

p_11 = subplot(3,2,1);
hold (p_11, 'on')
pl_1 = plot(p_11, x, TP9);
title('TP9');

p_12 = subplot(3,2,2);
hold (p_12, 'on')
pl_2 = plot(p_12, x, AF7);
title('AF7')

p_13 = subplot(3,2,3);
hold (p_13, 'on')
pl_3 = plot(p_13, x, AF8);
title('AF8');

p_21 = subplot(3,2,4);
hold (p_21, 'on')
pl_4 = plot(p_21, x, TP10);
title('TP10')


p_22 = subplot(3,2,5);
hold (p_22, 'on')
pl_5 = plot(p_22, x, RAUX);
title('RAUX')

p_23 = subplot(3,2,6);
hold (p_23, 'on')
pl_6 = plot(p_23, 1:size(x,2), x);
title('Time Stamps per sample');

i=0;
udp_sock.ByteOrder = 'littleEndian';

flushinput(udp_sock)

D = parallel.pool.DataQueue;
D.afterEach(@(display_arr) updateSurface(pl_1,pl_2,pl_3,pl_4,pl_5,pl_6, display_arr));

while (ishandle(dialogBox))
    if udp_sock.BytesAvailable ~= 0
        i=i+1;
        
        
        A = fread(udp_sock, 6, 'single');
        if size(A,1) ~= 6
            continue
        end
        
        
        prv_A = A(6);
        display_arr(:,1:end-1) = display_arr(:,2:end);
        display_arr(:,end) = A;
        display_arr(6,end)=display_arr(6,end)+display_arr(6,end-1);
        
        if (~mod(i,150)) 
            send(D, display_arr);
        end
        
        
        
        
    else
        pause(0.2)
    end

end
disp ('Done')
fclose (udp_sock);


