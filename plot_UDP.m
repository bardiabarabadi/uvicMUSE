clear all
close all

dialogBox = uicontrol('Style', 'PushButton', 'String', 'Break','Callback', 'delete(gcbf)');

PORT = 13;
udp_sock = udp('localhost',PORT, 'localport', PORT);
fopen (udp_sock);

display_arr = zeros ([6,500]);

ok=0;
TP9=0;
AF7=0;
AF8=0;
TP10=0;
TS=0;
RAUX=0;
A = zeros([6,1]);
prv_A = 0;

x = display_arr(6,:);
TP9 = display_arr(1,:);
AF7 = display_arr(2,:);
AF8 = display_arr(3,:);
TP10 = display_arr(4,:);
RAUX = display_arr(5,:);

p_11 = subplot(3,2,1);
p_12 = subplot(3,2,2);
p_13 = subplot(3,2,3);
p_21 = subplot(3,2,4);
p_22 = subplot(3,2,5);
p_23 = subplot(3,2,6);

pl_1 = plot(p_11, x, TP9);
pl_2 = plot(p_12, x, AF7);
pl_3 = plot(p_13, x, AF8);
pl_4 = plot(p_21, x, TP10);
pl_5 = plot(p_22, x, RAUX);
pl_6 = plot(p_23, 1:size(x,2), x);

pl_1.XDataSource = 'x';
pl_2.XDataSource = 'x';
pl_3.XDataSource = 'x';
pl_4.XDataSource = 'x';
pl_5.XDataSource = 'x';

pl_1.YDataSource = 'TP9';
pl_2.YDataSource = 'AF7';
pl_3.YDataSource = 'AF8';
pl_4.YDataSource = 'TP10';
pl_5.YDataSource = 'RAUX';
pl_6.YDataSource = 'x';


while (ishandle(dialogBox))

    if udp_sock.BytesAvailable ~= 0

        A = fscanf(udp_sock, '%f, %f, %f, %f, %f, %f\n');
        if size(A,1) ~= 6
            continue
        end
        if A(6) < prv_A
            continue
        end
        prv_A = A(6);
        display_arr(:,1:end-1) = display_arr(:,2:end);
        display_arr(:,end) = A;
        
        x = display_arr(6,:);
        TP9 = display_arr(1,:);
        AF7 = display_arr(2,:);
        AF8 = display_arr(3,:);
        TP10 = display_arr(4,:);
        RAUX = display_arr(5,:);
        
        refreshdata
        drawnow
        
    end

    pause(0.01);
end
disp ('Done')
fclose (udp_sock);


