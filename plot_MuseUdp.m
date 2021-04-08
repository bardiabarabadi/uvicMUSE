clear
clc
close all
figure 

dialogBox = uicontrol('Style', 'PushButton', 'String', 'Break','Callback', 'delete(gcbf)');

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
title('RAUX')

p_23 = subplot(3,2,6);
hold (p_23, 'on')
pl_6 = plot(p_23, x);
title('TIME');

i=0;

mu = MuseUdp();
methods(mu);

D = parallel.pool.DataQueue;
D.afterEach(@(display_arr) updateSurface(pl_1,pl_2,pl_3,pl_4,pl_5,pl_6, display_arr));

while (ishandle(dialogBox))
    
    [data, timestamp, success] = mu.get_eeg_sample();
    
    if success
        i=i+1;
        
        display_arr(:,1:end-1) = display_arr(:,2:end);
        display_arr(1:4,end) = data(1:4);
        display_arr(5,end) = -1;
        c=clock;
        display_arr(6,end) = c(6);
        
        if (~mod(i,150)) % Calling the updatesurface function every 150 samples
            send(D, display_arr);
        end
        
    else
        pause(0.002) % Wait for the buffer to fill if it is empty
    end

end
disp ('Done')

