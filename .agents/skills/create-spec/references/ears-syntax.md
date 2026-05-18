# Easy Approach to Requirements Syntax (EARS)

Use EARS format to write specifications.

## Syntax

The clauses of a requirement written in EARS always appear in the same order. The basic structure of an EARS requirement is:

```
While <optional pre-condition>, when <optional trigger>, the <system name> shall <system behaviour>
```

An EARS requirement must have:

- 0 or many preconditions
- 0 or 1 trigger
- 1 system name
- 1 or many system behaviours.

## Patters

### Ubiquitous requirements

Specify behaviours that are always active.

Syntax: The <system name> shall <system behaviour>

Example: The mobile phone shall have a mass of less than XX grams.

### State driven requirements

Specify behaviours active as long as the specified precondition(s) denoted by keyword `While` remains true.

Syntax: While <precondition(s)>, the <system name> shall <system behaviour>

Example: While there is no card in the ATM, the ATM shall display “insert card to begin”.

### Event driven requirements

Specify how a system must behave one or more triggering event denoted by keyword `When` occurs.

Syntax: When <trigger>, the <system name> shall <system behaviour>

Example: When “mute” is selected, the laptop shall suppress all audio output.

### Optional feature requirements

Apply in systems that include the specified feature(s) and are denoted by the keyword `Where`.

Syntax: Where <feature(s) included>, the <system name> shall <system behaviour>

Example: Where the car has a sunroof, the car shall have a sunroof control panel on the driver door.

### Unwanted behaviour requirements

Specify a system response to undesired situations and are denoted by the keywords `If` and `Then`.

Syntax: If <trigger>, then the <system name> shall <system behaviour>

Example: If an invalid credit card number is entered, then the website shall display “please re-enter credit card details”.

### Complex requirements

The simple building blocks of the EARS patterns described above can be combined to specify requirements for richer system behaviour.  Requirements that include more than one EARS keyword are called Complex requirements.

While <precondition(s)>, When <trigger(s)>, the <system name> shall <system behaviour>

Examples:

- While the aircraft is on ground, when reverse thrust is commanded, the engine control system shall enable reverse thrust.

Complex requirements for unwanted behaviour also include the If-Then keywords.


