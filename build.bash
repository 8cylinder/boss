
# To install packages for use by boss, eg:
# pip3 install click --target boss/deps

PROJECT_ROOT="$HOME/projects/boss/boss"
BOSS_DIR='src'
BOSS_APP='boss'

cd $PROJECT_ROOT

# remove any pycache dirs created while testing
for d in $(find -iname '__pycache__' -type d); do
    rm -rf "$d"
done

if [[ -e $BOSS_APP ]]; then
    rm $BOSS_APP
fi

if python3 -m zipapp --compress --python "/usr/bin/env python3" --output=$BOSS_APP $BOSS_DIR; then
    echo "$BOSS_APP built, $(du -h $PROJECT_ROOT/$BOSS_APP | cut -f1)"
fi
