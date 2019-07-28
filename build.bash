
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

if python3 -m zipapp --compress --python "/usr/bin/env python3" --output=$BOSS_APP $BOSS_DIR; then
    echo "Boss built, $(du -h $PROJECT_ROOT/boss.pyz | cut -f1)"
fi
