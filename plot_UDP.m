clear
clc
close all
figure 

dialogBox = uicontrol('Style', 'PushButton', 'String', 'Break','Callback', 'delete(gcbf)');

PORT = 1963;
EEG_OFFSET = 0;
PPG_OFFSET = 1;
ACC_OFFSET = 2;
GYRO_OFFSET = 3;

udps=instrfindall;

for u = 1:size(udps,2)
    u_port = udps(u).RemotePort;
    if u_port >= PORT && u_port <= PORT+GYRO_OFFSET
        delete (udps(u))
    end
end

udp_sock_eeg = udp('localhost',PORT+EEG_OFFSET, 'localport', PORT+EEG_OFFSET);
udp_sock_ppg = udp('localhost',PORT+PPG_OFFSET, 'localport', PORT+PPG_OFFSET);
fopen (udp_sock_eeg);
fopen (udp_sock_ppg);

display_arr = ones ([6,1000]);

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
pl_1 = plot(p_11, TP9);
title('TP9');

p_12 = subplot(3,2,2);
hold (p_12, 'on')
pl_2 = plot(p_12, AF7);
title('AF7')

p_13 = subplot(3,2,3);
hold (p_13, 'on')
pl_3 = plot(p_13, AF8);
title('AF8');

p_21 = subplot(3,2,4);
hold (p_21, 'on')
pl_4 = plot(p_21, TP10);
title('TP10')


p_22 = subplot(3,2,5);
hold (p_22, 'on')
pl_5 = plot(p_22, RAUX);
title('PPG[0]')

p_23 = subplot(3,2,6);
hold (p_23, 'on')
pl_6 = plot(p_23, x);
title('PPG[1]');

i=0;
udp_sock_eeg.ByteOrder = 'littleEndian';

flushinput(udp_sock_eeg)

D = parallel.pool.DataQueue;
D.afterEach(@(display_arr) updateSurface(pl_1,pl_2,pl_3,pl_4,pl_5,pl_6, display_arr));

while (ishandle(dialogBox))
    if udp_sock_eeg.BytesAvailable ~= 0 || udp_sock_ppg.BytesAvailable ~= 0
        i=i+1;
        
        
        A = fread(udp_sock_eeg, 6, 'single');
        %B = fread(udp_sock_ppg, 4, 'single');
        if size(A,1) ~= 6 %|| size(B,1) ~= 4
            continue
        end
        
        
        prv_A = A(6);
        display_arr(:,1:end-1) = display_arr(:,2:end);
        display_arr(1:4,end) = A(1:4);
        %display_arr(5:6,end) = B(1:2);
        
        if (~mod(i,150)) 
            send(D, display_arr);
        end
        
        
        
        
    else
        pause(0.002)
    end

end
disp ('Done')
fclose (udp_sock_eeg);
fclose (udp_sock_ppg);


