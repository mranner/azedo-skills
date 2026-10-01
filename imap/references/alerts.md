# imap - Alert-Mails in der Triage

**Inhalt:** Ist-Zustand prüfen, bevor ein Alert als Befund gemeldet wird · Alert-Paare

## Alert-Mails gegenprüfen, nicht weiterreichen

Monitoring- und Reminder-Mails beschreiben einen **vergangenen** Zustand. Bevor
so eine Mail als Befund gemeldet oder gepusht wird, den Ist-Zustand prüfen:

```
# sshd-Alert -- antwortet der Port jetzt?
nc -z -w 5 <host> 22

# Zertifikats-Reminder -- welches Cert läuft dort wirklich?
echo | openssl s_client -servername <host> -connect <host>:443 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

Das ändert die Bewertung regelmäßig: ein "Wildcard läuft morgen ab" ist
harmlos, wenn der Host längst ein Let's-Encrypt-Zertifikat ausliefert -- und
ein Alert ohne Recovery-Mail ist erledigt, wenn der Dienst wieder antwortet.
Umgekehrt gilt: **Alert-Paare erst nach einem Monitoring-Intervall bewerten**
(monit schickt die Recovery typisch nach ~2 Minuten), sonst wird jedes
Failed-Alert einmal zu früh als offener Befund gemeldet.
