---
name: refactor
description: Refactors code to improve its design, structure, and maintainability without changing its behavior. Use this skill when you identify code that could be improved in terms of readability, simplicity, or adherence to design principles, and you want to refactor it to enhance its quality.
---
# Guidelines 

Below you will find known code smells to help you discover code that needs improvement, together with hints on how to improve it. Consider all the following code smells below as **potential** (but not necessarily) design problems.

After identifying any of the following smells in the code, refactor only if the resulting code would be simpler, more straightforward and more succinct. Smell identification is not a permission to refactor unless the effect is material and observable.

Avoid refactoring when the code is already clear, simple, or only aesthetically imperfect, when the refactoring will introduce more complexity than the problem justifies, or changes public APIs, even if the code manifests any of the identified code smells.

Prefer the smallest safe refactoring first. Introduce patterns such as STRATEGY, COMMAND, or VISITOR only when structurally simpler refactorings leave the underlying problem unresolved.

Before refactoring verify that the affected area is covered by tests. If tests are missing, add them first. After the refactoring, behavior must remain *unchanged*.

When refactoring ensure code correctness first, simplicity, readability and clarity next.

Note: Words in CAPITAL LETTERS in this document (i.e. FACTORY METHOD, STRATEGY, COMPOSITE, etc.) identify GoF design patterns.

## Code Smells

Treat any code showing any fo the following characteristics as candidate for refactoring.

### 1. Dupicated code

Identical code or code which is outwardly different yet serves the same intent and produces the same outcome.

Potential refactorings that fix it:

- **Extract Method:** When two code blocks duplicate intent, extract the duplicated behavior into a named method. Only introduce a pattern if simple extraction is not enough.
- **Parameterize Method:** When duplicate methods differ only by literals, constants, flags, or small values, collapse them into one parameterized method instead of introducing inheritance or strategy.
- **Form TEMPLATE METHOD:** When two methods in subclasses perform similar steps in the same order yet the steps are different, generalise the methods by extracting their steps ito methods with identical signatures, then pull up the generalized methods to form a TEMPLATE METHOD.
- **Pull-Up Method/Field:** When duplicated methods or fields exist across sibling subclasses, move the common behavior or state to the superclass. TEMPLATE METHOD handles similar algorithms with variable steps, but identical behavior should often just be pulled up.
- **Introduce polymorphic creation with FACTORY METHODs:** When classses in a hierarchy implement a method similarly except for an object cretion step, make a single superclass version of the method that calls a FACTORY METHOD to handle the instantiation.
- **Chain constructors:** When you have multiple constuructors that contain duplicate code, chain constructors together to obtain the least amount of duplicated code. Important: first, try to resolve duplication by using default constructor arguments if possible in the programming language.
- **Extract COMPOSITE:** When sublasses in a hierarchy implement the same COMPOSITE, extract a superclass that implements the COMPOSITE.
- **Unify interfaces with ADAPTER:** When clients interact with two classes one of which has a preferred interface, unify the interfaces with an ADAPTER.

### 2. Long method

As a guideline, every method more than 10 lines of code (ignoring empty lines) should be treated as a suspect and evaluated accordingly. However, a method longer than 10 lines does not mean that it should be refactored. The final decision should taken based on it includes more than one reasons to change and if decomposing it in smaller methods, each with a single responsibility, would make the code more simple, clear and succinct.

Potential refactorings that fix it:

- **Extract Method.**
- **Replace Temp with Query:** When temporary variables make a long method hard to split, replace derived temporary values with query methods.
- **Replace Method with Method Object:** When a method is too tangled with local variables to extract cleanly, move the method body into a helper object where local variables become fields, then decompose the behavior inside that object. 
- **Split Loop:** When one loop performs multiple unrelated tasks, split it into separate loops, each with one clear responsibility.
- **Compose Method:** When you can't rapidly understand a method's logic, transform the logic into a small number of intention-revealing steps at the same level of detail.
- **Move Accumulation to Collecting Parameter:** When you have a single buly method that accumulates information to a local variable, accumulate results to a Collecting Parameter that gets passed to extracted methods.
- **Replace Conditional Dispatcher with COMMAND:** When conditional logic is used to dispatch requests and execute actions, create a COMMAND for each action. Store the COMMANDs in a collation and replace the conditional logic with code to fetch and execute COMMANDs.
- **Move Accumulation to VISITOR:** When a method accumulates information from heterogeneous classes, move the accumulation task to a VISITOR that can visit each class to accumulate the information.
- **Replace Conditional Logic with STRATEGY:** When conditional logic in a method controls which of several variantes of a calculation are executed, create a STRATEGY for each variant and make the method delegate the calculation to a STRATEGY instance.

### 3. Conditional complexity

Potential refactorings that fix it:

- **Decompose Conditional:** When a conditional expression or its branches are hard to understand, extract the condition and each branch into intention-revealing methods.
- **Consolidate Conditional Expression:** When multiple conditional checks lead to the same result, then combine them behind a single intention-revealing predicate.
- **Replace Type Code with Subclasses / Polymorphism:** When conditionals repeatedly branch based on an object’s type, kind, or category, move the variant behavior into subclasses or polymorphic implementations.
- **Replace Conditional Logic with STRATEGY.**
- **Move Embellishment to DECORATOR:** When the code provides an embellisment to a class's core responsibility, move the embellishment code to a DECORATOR.
- **Replace State-Altering Conditionals with STATE:** When the conditional expressions that control an object's state transitions are complex, replace the conditionals with STATE classes that handle specific states and transitions between them.
- **Introduce Null Object:**

### 4. Primitive obsession

Potential refactorings that fix it:

- **Introduce Value Object:** When primitives represent meaningful domain concepts such as money, IDs, sizes, codes, or statuses, replace them with small domain-specific value objects that enforce invariants.
- **Replace Data Clump with Parameter Object:** When the same group of values repeatedly appears together in method signatures, wrap them in a meaningful parameter object.
- **Replace Magic Number/String with Named Constant or Enum:** When unexplained literals encode domain meaning, replace them with named constants or enums.
- **Encapsulate Collection:** When raw collections are passed around despite having domain rules or invariants, wrap the collection in a domain-specific object.
- **Replace Type Code with Enum/Class:** When a field's type (e.g. String or int) fails to protect it from unsafe assignments and invalid equality comparisons, constraint the assignments and equality comparisons by making its type an enum or class.
- **Replace State-Altering Conditionals with STATE.**
- **Replace Conditional Logic with STRATEGY.**
- **Replace Implicit Tree with COMSPOSITE:** When you impicitly form a tree structure using a primitive representation such as a String, replace your primitive representation with a COMPOSITE.
- **Replace Implicit Language with INTERPRETER or a domain-specific language:** When numerous methods on a class combine elements of an implicit language, define classes for elements of the implicit language so that instances may be combines to form interpretable expressions.
- **Move Embellishment to DECORATOR.**
- **Encapsulate Composite with BUILDER:** When building a COMPOSITE is repetitive complicated and error-prone, simplify the build by letting a BUILDER handle the details.

### 5. Indecent exposure

Breach of information hiding. When methods or classes that ought not to be visible to clients are accessible to them. As a ground rule, always use the stricter visibility needed for classes and class members. Give access to them only when clients trully need them.

Potential refactorings that fix it:

- **Encapsulate Field:** When fields are publicly visible or too easily mutated by clients, hide them behind methods or properties that preserve object invariants.
- **Encapsulate Collection.**
- **Hide Delegate:** When clients navigate through an object to reach its collaborators, add forwarding methods on the owning object and hide the collaborator chain.
- **Encapsulate Classes with FACTORY:** When clients directly instantiate classes that reside in one package and implement common interfaces, make the class constructors non-public and let clients created instances of them using a FACTORY.

### 6. Solution sprawl

Violation of single responsibility principle. Responsibility becomes sprawled across numerous classes.

Potential refactorings that fix it:

- **Move Method/Field:** When behavior or state lives far from the data or concept it belongs to, move it to the class that owns the relevant responsibility.
- **Extract Class:** When one class contains multiple responsibilities that change for different reasons, extract a cohesive responsibility into a separate class.
- **Introduce Facade:** When many clients coordinate the same group of classes in the same way, introduce a facade that centralizes the workflow.
- **Move Creation Kowledge to FACTORY:** When data and code used to instantiate a class is sprawled across numerous classes, move the creation knowledge into a single FACTORY class.

### 7. Alternative classes with diferent interfaces

Potential refactorings that fix it:

- **Rename Method/Class:** When alternative classes differ mainly because they use inconsistent vocabulary, rename methods or classes to align the model before adding an adapter.
- **Extract Interface:** When alternative classes provide the same capability but lack a shared contract, extract an interface that captures the common role.
- **Unify interfaces with ADAPTER.**

### 8. Lazy class

Potential refactorings that fix it:

- **Inline Class:** When a class no longer carries enough responsibility to justify its existence, then merge its behavior into the class that uses it most.
- **Inline SINGLETON:**

### 9. Large class

Potential refactorings that fix it:

- **Extract Class.**
- **Move Method/Field**
- **Extract Superclass/Interface:** When a large class exists because it serves several roles or shares behavior with related classes, then extract a superclass or role-specific interface.
- **Replace Conditional Dispatcher with COMMAND.**
- **Replace State-Altering Conditionals with STATE.**
- **Replace Implicit Language with INTERPRETER or a domain-specific language.**

### 10. Switch statements

Potential refactorings that fix it:

- **Replace Conditional with Polymorphism:** When a switch chooses behavior based on type, state, or category, move the behavior to polymorphic implementations.
- **Replace Type Code with Subclasses:** When a switch repeatedly branches on the same type-code field, replace the type code with subclasses or sealed variants.
- **Replace Conditional Dispatcher with COMMAND.**
- **Move Accumulation to VISITOR.**

### 11. Combinatorial explosion

Potential refactorings that fix it:

- **Replace Inheritance with Composition:** When many subclasses exist only to represent combinations of features, replace the inheritance hierarchy with composable collaborators.
- **Introduce Parameter Object or Configuration Object:** When combinations are driven by sets of options, model the options explicitly instead of creating one class or method per combination.
- **Replace Implicit Language with INTERPRETER or a domain-specific language.**

### 12. Oddball solution

Potential refactorings that fix it:

- **Substitute Algorithm:** When one implementation solves the same problem differently from the rest of the codebase, replace it with the standard algorithm already used elsewhere.
- **Extract Shared Abstraction:** When several implementations solve the same conceptual problem with different structures, extract a common abstraction and migrate callers toward it.
- **Unify interfaces with ADAPTER.**
