const int led = 15;  // GPIO 15 (GP15)

void setup() {
  pinMode(led, OUTPUT);
}

void loop() {
  digitalWrite(led, HIGH);  // LED on
  delay(1000);              // Wait 1 second

  digitalWrite(led, LOW);   // LED off
  delay(1000);              // Wait 1 second
}
