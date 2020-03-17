function updateSurface(pl_1,pl_2,pl_3,pl_4,pl_5,pl_6, display_arr)

x = display_arr(6,:);
TP9 = display_arr(1,:);
AF7 = display_arr(2,:);
AF8 = display_arr(3,:);
TP10 = display_arr(4,:);
RAUX = display_arr(5,:);


pl_1.YData = TP9;
pl_2.YData = AF7;
pl_3.YData = AF8;
pl_4.YData = TP10;
pl_5.YData = RAUX;
pl_6.YData = x;
drawnow

end