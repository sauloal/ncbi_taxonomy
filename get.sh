wget \
--no-clobber --continue --no-directories --no-host-directories --no-parent \
--reject '*.zip' --reject '*_diff.zip' --reject '*_diff.dmp.gz' --reject '*.Z' --reject '*.md5' \
ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/*

mkdir -p taxdump
tar --directory taxdump -xvf taxdump.tar.gz

mkdir -p taxcat
tar --directory taxcat -xvf taxcat.tar.gz


grep '|$' taxdump/citations.dmp
