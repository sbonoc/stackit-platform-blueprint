#!/usr/bin/env bash
# Source: adds function foo

bar() {
    echo "bar"
}

function foo {
    echo "foo"
}

bar
foo
