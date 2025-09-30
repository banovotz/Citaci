Ova skripta generira raspored čitača za nedjeljna čitanja na sv. misi.

* citaci_grupe.json definira grupe čitača po vremenu mise (npr: 9:00, 10:30, 19:00).
* Program generira sljedećih N nedjelja (parametar num_weeks).
* Nasumično dodjeljuje 1., 2. čitanje i molitvu vjernika unutar grupe.
* Čitač neće čitati dvije nedjelje za redom (ukoliko je to moguće obzirom na broj čitača u grupi) 
* Čitač neće doći na red sve dok se svi čitači iz grupe ne izmjene. 
* Rezultat se sprema u raspored.html kao tablica.

* pokretanje:
`` 
$ python3 script.py <date> <nr_of_sundays>
`` 
   * eg:
`` 
python3 script.py "2025/10/05" 6
`` 


