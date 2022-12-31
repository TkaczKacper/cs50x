-- Keep a log of any SQL queries you execute as you solve the mystery.
SELECT * FROM crime_scene_reports WHERE year=2021 AND month=7 AND day=28 AND street="Humphrey Street";
SELECT * FROM interviews WHERE year=2021 AND month=7 AND day=28 AND transcript LIKE '%bakery%';
SELECT * FROM bakery_security_logs WHERE year=2021 AND month=7 AND day=28 AND hour=10 AND minute BETWEEN 0 AND 25;
SELECT * FROM flights LEFT JOIN airports ON flights.origin_airport_id=airports.id WHERE airports.city="Fiftyville" AND year=2021 AND month=7 AND day=29 ORDER BY hour;
SELECT * FROM passengers WHERE flight_id=36;
SELECT * FROM people WHERE passport_number IN (SELECT passport_number FROM passengers WHERE flight_id=36) AND license_plate IN (SELECT license_plate FROM bakery_security_logs WHERE year=2021 AND month=7 AND day=28 AND hour=10 AND minute BETWEEN 0 AND 25);
SELECT * FROM atm_transactions WHERE account_number IN (SELECT account_number FROM bank_accounts WHERE person_id IN (SELECT id FROM people WHERE passport_number IN (SELECT passport_number FROM passengers WHERE flight_id=36) AND license_plate IN (SELECT license_plate FROM bakery_security_logs WHERE year=2021 AND month=7 AND day=28 AND hour=10 AND minute BETWEEN 0 AND 25))) AND transaction_type='withdraw';
SELECT * FROM bank_accounts WHERE person_id IN (SELECT id FROM people WHERE passport_number IN (SELECT passport_number FROM passengers WHERE flight_id=36) AND license_plate IN (SELECT license_plate FROM bakery_security_logs WHERE year=2021 AND month=7 AND day=28 AND hour=10 AND minute BETWEEN 0 AND 25));
SELECT * FROM phone_calls WHERE year=2021 AND month=7 AND day=28 AND duration < 60 AND caller='(367) 555-5533';
SELECT * FROM people WHERE phone_number='(375) 555-8161';