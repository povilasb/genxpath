# About

An interactive XPath generator and testing tool for web scraping and HTML parsing.

## Features

- **Interactive Shell**: Query, test, and minimize XPath expressions
- **Smart XPath Generation**: Automatically find XPath expressions for given text values
- **XPath Minimization**: Optimize XPath expressions to their shortest unique form
- **Multiple Input Sources**: Works with local HTML files or remote URLs
- **Caching**: Built-in caching for remote content to speed up development

## Installation

```bash
uv sync
```

## Usage

### Command Line

```bash
# Load from URL
genxpath https://example.com

# Load from local file
genxpath path/to/file.html
```

### Interactive Commands

Once in the interactive shell:

- `q <xpath>` - Query an XPath expression
- `m <xpath>` - Minimize an XPath to its shortest form
- `f <text>` - Find XPath expressions for specific text
- `d` - Display the loaded HTML document

## Example

```bash
$ genxpath https://example.com
HELP:
   q - query xpath
   m - minimize xpath
   f - find xpath by value
   d - print loaded document

> f "Welcome to Example"
//h1/text()
//div[@class="welcome"]/text()

> q //h1
0: <h1>Welcome to Example</h1>

> m //html/body/div[1]/h1
//h1
```

## Architecture

* `genxpath/_gen.py` - core algorithms.
* `genxpath/gui.py` - [Textual](https://textual.textualize.io/) based TUI.
* `genxpath/__main_.py` - interactive CLI.
