clear all;

%% Daten laden
load('laufzeit_log_flur')
load('laufzeit_wlan_zuhause')

%% Haeufigkeiten ermitteln und Laufzeiten in ms umrechnen
[ h1(:,2), h1(:,1) ] = hist(laufzeit_log_flur, 500);
h1(:,1) = h1(:,1)*1e3;
h1(:,2) = h1(:,2)/max(h1(:,2));

[ h2(:,2), h2(:,1) ] = hist(laufzeit_wlan_zuhause, 1000);
h2(:,2) = h2(:,2)/max(h2(:,2));

%% Logarithmischer Plot der Laufzeithaeufigkeiten
semilogx(h1(:,1), h1(:,2),  'g'); grid on; hold on;
semilogx(h2(:,1), h2(:,2),  'b');
title('Normiertes Histogramm der Signallaufzeiten'); legend('Bluetooth', 'WLAN'); xlabel('Laufzeit / ms');
xlim([1, 100]);  ylim([0 1.1]);

%% Optische anpassungen
xtick = [ 1:10, 20:10:100 ];
xticklabel = { '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '20', '30', '40', '50', '60', '70', '80', '90', '100' };
set(gcf, 'Position', [200 200 900 200]);
set(gca, 'xtick', xtick);
set(gca, 'xticklabel', xticklabel);
